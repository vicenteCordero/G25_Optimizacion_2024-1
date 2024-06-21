from main import main


def variar(i):
    main(f"data/var{i}.json")


if __name__ == "__main__":
    n = input()
    variar(n)