import requests
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict

def get_interest_rates():
    url = 'https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml'
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to fetch data")
        return None

    root = ET.fromstring(response.content)

    # Prepare CSV file
    with open("interest_rates.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["year-month", "interest_rate"])

        for pozycje in root.findall("pozycje"):
            date_str = pozycje.attrib["obowiazuje_od"]
            year_month = "-".join(date_str.split("-")[:2])  # YYYY-MM
            ref_rate = None

            for pozycja in pozycje.findall("pozycja"):
                if pozycja.attrib["id"] == "ref":
                    # Convert 24,50 → 24.50
                    ref_rate = pozycja.attrib["oprocentowanie"].replace(",", ".")
                    break

            if ref_rate is not None:
                writer.writerow([year_month, ref_rate])

    print("Data saved to interest_rates.csv")

#get_interest_rates()


def analyze_interest_rates(csv_file="interest_rates.csv"):
    # Load data from CSV
    data = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append((row["year-month"], float(row["interest_rate"])))

    # Convert year-month to full date (assume 1st day of month)
    dates = [datetime.strptime(d + "-01", "%Y-%m-%d") for d, _ in data]

    # Calculate duration of each rate
    durations = []  # (interest_rate, num_days)
    for i in range(len(data)):
        rate = data[i][1]
        start = dates[i]
        if i < len(data) - 1:
            end = dates[i+1]
        else:
            end = datetime.now()  # last period until today
        days = (end - start).days
        durations.append((rate, days))

    # Aggregate by interest rate
    rate_days = defaultdict(int)
    total_days = 0
    weighted_sum = 0.0

    for rate, days in durations:
        rate_days[rate] += days
        total_days += days
        weighted_sum += rate * days

    # Sort by number of days
    sorted_rates = sorted(rate_days.items(), key=lambda x: x[1], reverse=True)

    # Print table
    print(f"{'Rate':>10} | {'Days':>10}")
    print("-" * 23)
    for rate, days in sorted_rates:
        print(f"{rate:>10.2f} | {days:>10}")

    # Calculate weighted average
    avg_rate = weighted_sum / total_days
    print(f"\nWeighted average interest rate across the whole time: {avg_rate:.2f}%")

def calculate_yearly_average(input_csv="interest_rates.csv", output_csv="interest_rates_yearly_avg.csv"):
    yearly_rates = defaultdict(list)

    # Read the CSV
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = row["year-month"].split("-")[0]
            yearly_rates[year].append(float(row["interest_rate"]))

    # Calculate yearly averages
    yearly_avg = []
    for year, rates in yearly_rates.items():
        avg_rate = sum(rates) / len(rates)
        yearly_avg.append((year, avg_rate))

    # Sort by year
    yearly_avg.sort(key=lambda x: x[0])

    # Save to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "average_interest_rate"])
        writer.writerows(yearly_avg)

    print(f"Yearly averages saved to {output_csv}")

# Example usage
calculate_yearly_average()
