from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eazydatafix.models.agentic_eda_result import VisualisationRecommendation
from eazydatafix.reporting.agentic_eda.charts.base import (
    ChartContext,
    ChartDataUnavailableError,
    ChartHandler,
)


class MissingValueChartHandler(ChartHandler):
    """Generates a missing-value bar chart from execution output."""

    type = "missing_value_chart"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        affected = context.step_outputs.get(recommendation.source_step, {}).get(
            "affected_columns",
            [],
        )

        if not affected:
            raise ChartDataUnavailableError(
                "Missing-value execution output contains no affected columns."
            )

        labels = [str(item["column"]) for item in affected]
        values = [int(item["count"]) for item in affected]
        plt = self.pyplot()
        figure, axis = plt.subplots(figsize=(max(6, len(labels) * 1.1), 4))
        axis.bar(labels, values, color="#2563eb")
        axis.set_title("Missing values by column")
        axis.set_ylabel("Missing value count")
        axis.tick_params(axis="x", rotation=35)
        figure.tight_layout()
        self.save_figure(figure, output_path)


class DistributionBarChartHandler(ChartHandler):
    """Generates categorical or boolean bar charts from execution output."""

    type = "bar_chart"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        column = _single_column(recommendation)
        metrics = _column_metrics(context, recommendation.source_step, column)

        if recommendation.source_step == "categorical_distribution_analysis":
            frequencies = metrics.get("frequency_counts", {})
            labels = list(frequencies)
            values = [int(frequencies[label]) for label in labels]
            title = f"Categorical distribution: {column}"
        elif recommendation.source_step == "boolean_distribution_analysis":
            labels = ["True", "False", "Missing"]
            values = [
                int(metrics.get("true_count", 0)),
                int(metrics.get("false_count", 0)),
                int(metrics.get("missing_count", 0)),
            ]
            title = f"Boolean distribution: {column}"
        else:
            raise ChartDataUnavailableError(
                f"Bar chart source step '{recommendation.source_step}' is not supported."
            )

        if not labels:
            raise ChartDataUnavailableError(f"No distribution values are available for {column}.")

        _bar_chart(self, labels, values, title, output_path)


class ClassDistributionChartHandler(ChartHandler):
    """Generates class distribution charts from full structured distributions."""

    type = "class_distribution_chart"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        column = _single_column(recommendation)
        categorical = context.step_outputs.get("categorical_distribution_analysis", {}).get(
            "columns",
            {},
        )
        boolean = context.step_outputs.get("boolean_distribution_analysis", {}).get(
            "columns",
            {},
        )

        if column in categorical:
            frequencies = categorical[column].get("frequency_counts", {})
            labels = list(frequencies)
            values = [int(frequencies[label]) for label in labels]
        elif column in boolean:
            metrics = boolean[column]
            labels = ["True", "False"]
            values = [
                int(metrics.get("true_count", 0)),
                int(metrics.get("false_count", 0)),
            ]
        else:
            raise ChartDataUnavailableError(
                f"A complete class distribution is not available for {column}."
            )

        if not labels:
            raise ChartDataUnavailableError(f"No class values are available for {column}.")

        _bar_chart(
            self,
            labels,
            values,
            f"Class distribution: {column}",
            output_path,
            color="#dc2626",
        )


class HistogramChartHandler(ChartHandler):
    """Generates numeric histograms when a validated dataset is supplied."""

    type = "histogram"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        values, column = _raw_numeric_values(recommendation, context)
        plt = self.pyplot()
        figure, axis = plt.subplots(figsize=(7, 4))
        bins = max(1, min(20, int(np.sqrt(len(values))) or 1))
        axis.hist(values, bins=bins, color="#7c3aed", edgecolor="white")
        axis.set_title(f"Numeric histogram: {column}")
        axis.set_xlabel(column)
        axis.set_ylabel("Frequency")
        figure.tight_layout()
        self.save_figure(figure, output_path)


class BoxPlotChartHandler(ChartHandler):
    """Generates numeric box plots when a validated dataset is supplied."""

    type = "box_plot"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        values, column = _raw_numeric_values(recommendation, context)
        plt = self.pyplot()
        figure, axis = plt.subplots(figsize=(7, 3.5))

        try:
            axis.boxplot(values, orientation="horizontal")
        except TypeError:
            axis.boxplot(values, vert=False)

        axis.set_title(f"Box plot: {column}")
        axis.set_xlabel(column)
        figure.tight_layout()
        self.save_figure(figure, output_path)


class CorrelationHeatmapHandler(ChartHandler):
    """Generates a correlation heatmap from structured execution output."""

    type = "correlation_heatmap"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        matrix = context.step_outputs.get(recommendation.source_step, {}).get("matrix", {})
        columns = [column for column in recommendation.target_columns if column in matrix]

        if len(columns) < 2:
            raise ChartDataUnavailableError(
                "At least two correlated numeric columns are required for a heatmap."
            )

        values = np.array(
            [
                [
                    np.nan if matrix[column].get(related) is None else matrix[column][related]
                    for related in columns
                ]
                for column in columns
            ],
            dtype=float,
        )
        plt = self.pyplot()
        figure, axis = plt.subplots(figsize=(max(5, len(columns)), max(4, len(columns) * 0.8)))
        image = axis.imshow(values, cmap="coolwarm", vmin=-1, vmax=1)
        axis.set_xticks(range(len(columns)), labels=columns, rotation=35, ha="right")
        axis.set_yticks(range(len(columns)), labels=columns)
        axis.set_title("Correlation heatmap")

        for row_index in range(len(columns)):
            for column_index in range(len(columns)):
                value = values[row_index, column_index]
                label = "n/a" if np.isnan(value) else f"{value:.2f}"
                axis.text(column_index, row_index, label, ha="center", va="center", fontsize=8)

        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
        figure.tight_layout()
        self.save_figure(figure, output_path)


class DatetimeFrequencyChartHandler(ChartHandler):
    """Generates datetime frequency charts from structured trend output."""

    type = "time_series_line_chart"

    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        column = _single_column(recommendation)
        metrics = _column_metrics(context, recommendation.source_step, column)
        frequencies = metrics.get("month_frequency") or metrics.get("year_frequency") or {}

        if not frequencies:
            raise ChartDataUnavailableError(
                f"No datetime frequency summary is available for {column}."
            )

        labels = list(frequencies)
        values = [int(frequencies[label]) for label in labels]
        plt = self.pyplot()
        figure, axis = plt.subplots(figsize=(max(7, len(labels) * 0.8), 4))
        axis.plot(labels, values, marker="o", color="#059669")
        axis.set_title(f"Datetime frequency: {column}")
        axis.set_ylabel("Record count")
        axis.tick_params(axis="x", rotation=35)
        axis.grid(axis="y", alpha=0.25)
        figure.tight_layout()
        self.save_figure(figure, output_path)


def _single_column(
    recommendation: VisualisationRecommendation,
) -> str:
    if not recommendation.target_columns:
        raise ChartDataUnavailableError("The visualisation has no target columns.")

    return recommendation.target_columns[0]


def _column_metrics(
    context: ChartContext,
    source_step: str,
    column: str,
) -> dict[str, Any]:
    metrics = context.step_outputs.get(source_step, {}).get("columns", {}).get(column)

    if metrics is None:
        raise ChartDataUnavailableError(
            f"Structured execution output is unavailable for column {column}."
        )

    return metrics


def _raw_numeric_values(
    recommendation: VisualisationRecommendation,
    context: ChartContext,
) -> tuple[pd.Series, str]:
    column = _single_column(recommendation)

    if context.dataframe is None:
        raise ChartDataUnavailableError(
            f"{recommendation.type} for {column} requires the optional validated dataset."
        )

    if column not in context.dataframe.columns:
        raise ChartDataUnavailableError(f"Dataset column {column} is unavailable.")

    values = pd.to_numeric(context.dataframe[column], errors="coerce").dropna()

    if values.empty:
        raise ChartDataUnavailableError(f"No numeric values are available for {column}.")

    return values, column


def _bar_chart(
    handler: ChartHandler,
    labels: list[str],
    values: list[int],
    title: str,
    output_path: Path,
    color: str = "#0f766e",
) -> None:
    plt = handler.pyplot()
    figure, axis = plt.subplots(figsize=(max(6, len(labels) * 1.0), 4))
    axis.bar([str(label) for label in labels], values, color=color)
    axis.set_title(title)
    axis.set_ylabel("Count")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    handler.save_figure(figure, output_path)
