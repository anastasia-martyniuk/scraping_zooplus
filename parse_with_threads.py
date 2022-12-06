import csv
import threading
import time
from dataclasses import dataclass, astuple, fields


import requests

BASE_URL = "https://www.zooplus.de/tierarzt/results"

OUTPUT_CSV_PATH = "doctors.csv"


@dataclass
class Doctor:
    full_name: str
    clinic: str
    open_time: str
    address: str
    rating: int
    num_of_reviews: int


DOCTORS_FIELDS = [field.name for field in fields(Doctor)]


def parse_one_doctor(doctor) -> Doctor:
    return Doctor(
        full_name=doctor["name"],
        clinic=doctor["subtitle"]
        if "subtitle" in doctor
        else "sorry, we don't have this information",
        open_time=doctor["open_time"],
        address=doctor["address"],
        rating=doctor["avg_review_score"],
        num_of_reviews=doctor["count_reviews"],
    )


token = requests.get(
    "https://www.zooplus.de/tierarzt/api/v2/token?debug=authReduxMiddleware-tokenIsExpired"
).json()["token"]
headers = {"authorization": f"Bearer {token}"}


def get_doctors(num):
    all_doctors = []
    attribute_from = 0
    attribute_page = 1

    page = requests.get(
        "https://www.zooplus.de/tierarzt/api/v2/results",
        params={
            "animal_99": True,
            "page": {attribute_page},
            "from": {attribute_from},
            "size": 20,
        },
        headers=headers,
    )
    content = page.json()

    attribute_from += 20
    all_doctors += [parse_one_doctor(doctor) for doctor in content["results"]]

    with open(OUTPUT_CSV_PATH, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(DOCTORS_FIELDS)
        writer.writerows([astuple(doctor) for doctor in all_doctors])


def main_threads():
    tasks = []

    for num in range(1, 6):
        tasks.append(threading.Thread(target=get_doctors, args=(num,)))
        tasks[-1].start()

        for task in tasks:
            task.join()


if __name__ == "__main__":
    start_time = time.perf_counter()
    main_threads()
    end_time = time.perf_counter()
    print("Elapsed:", end_time - start_time)
