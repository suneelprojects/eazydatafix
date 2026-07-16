import easydatafix as edf

datasets = [
    "datasets/titanic.csv",
    "datasets/iris.csv",
    "datasets/penguins.csv",
    "datasets/tips.csv",
    "datasets/diamonds.csv",
]

for dataset in datasets:

    print("=" * 80)
    print(dataset)
    print("=" * 80)

    try:

        df = edf.analysis_ready(dataset)

        print(df.info())

        print()

        print(df.dtypes)

        print()

        print(df.head())

    except Exception as e:

        print("FAILED")
        print(e)

    print("\n")
