from get_data import generate_more
from sendfiles import sendback_file


def tocsv(df, i):
    df.to_csv(f"file{i}.csv",index=False)

def process():
    df1, df2, df3 = generate_more()
    tocsv(df1, 1)
    tocsv(df2, 2)
    tocsv(df3, 3)
    c = 0
    if sendback_file("file1.csv") == "Success":
        print("file1 sent.")
        c += 1
    if sendback_file("file2.csv") == "Success":
        print("file2 sent.")
        c += 1
    if sendback_file("file3.csv") == "Success":
        print("file3 sent.")
        c += 1

    if c == 3:
        print("All files sent successfully to local machine.")
    else:
        print("One of the files wasn't sent.")


if __name__ == "__main__":
    process()   