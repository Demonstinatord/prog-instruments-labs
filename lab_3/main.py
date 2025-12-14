from checksum import calculate_checksum, serialize_result
from dataprocessing import read_json, read_csv, validity_check


def main():
    try:
        settings = read_json("settings.json")
        data = read_csv(settings["csv_filename"])
        arr=validity_check(data, settings["regular_expressions"])
        checksum = calculate_checksum(arr)
        print("number of invalid lines",len(arr))
        print("checksum", checksum)
        serialize_result(settings["variant"], checksum, settings["result_filename"])
    except Exception as exc:
        print(f'Something went wrong: {exc}')


if __name__ == "__main__":
    main()