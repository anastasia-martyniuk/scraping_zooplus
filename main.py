import csv
import time
from dataclasses import dataclass, astuple, fields
import requests


BASE_URL = "https://www.zooplus.de/tierarzt/results"

OUTPUT_CSV_PATH = "r_bs4/doctors.csv"


@dataclass
class Doctor:
    full_name: str
    clinic: str
    open_time: dict
    address: str
    rating: int
    num_of_reviews: int


DOCTORS_FIELDS = [field.name for field in fields(Doctor)]


def parse_one_doctor(doctor) -> Doctor:
    open_time = {}

    for index, day in enumerate(doctor["open_time"]):
        if f"{day['day']}" in open_time.keys():
            continue

        if index == len(doctor["open_time"]) - 1:
            open_time.update({f'{day["day"]}': f'{day["from"]}-{day["to"]}'})
            break

        one_day = doctor["open_time"][index + 1]
        if day["day"] == one_day["day"]:
            open_time.update(
                {
                    f'{day["day"]}': f'{day["from"]}-{day["to"]}, {one_day["from"]}-{one_day["to"]}'
                }
            )
        else:
            open_time.update({f'{day["day"]}': f'{day["from"]}-{day["to"]}'})

    return Doctor(
        full_name=doctor["name"],
        clinic=doctor["subtitle"]
        if "subtitle" in doctor
        else "sorry, we don't have this information",
        open_time=open_time,
        address=doctor["address"],
        rating=doctor["avg_review_score"],
        num_of_reviews=doctor["count_reviews"],
    )


def get_doctors(num):
    token = requests.get(
        "https://www.zooplus.de/tierarzt/api/v2/token?debug=authReduxMiddleware-tokenIsExpired"
    ).json()["token"]
    headers = {"authorization": f"Bearer {token}"}

    all_doctors = []
    attribute_from = 0

    for attribute_page in range(1, num):
        page = requests.get(
            "https://www.zooplus.de/tierarzt/api/v2/results",
            params={
                "animal_99": "true",
                "page": {attribute_page},
                "from": {attribute_from},
                "size": 20,
            },
            headers=headers,
        )
        content = page.json()

        attribute_from += 20
        all_doctors += [parse_one_doctor(doctor) for doctor in content["results"]]

    return all_doctors


def write_to_csv(doctors: [Doctor]) -> None:
    with open(OUTPUT_CSV_PATH, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(DOCTORS_FIELDS)
        writer.writerows([astuple(doctor) for doctor in doctors])


if __name__ == "__main__":
    start_time = time.perf_counter()
    doc = get_doctors(6)
    write_to_csv(doc)
    end_time = time.perf_counter()
    print("Elapsed:", end_time - start_time)
