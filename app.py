# app.py

import os
import re
import io
import requests
import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, url_for
from bs4 import BeautifulSoup
from thefuzz import fuzz, process

# External dictionaries
from otoparts_dict import AVAILABLE_BRANDS_MODELS_OTOPARTS
from autopia_dict import AVAILABLE_BRANDS_MODELS_AUTOPIA

# Fuzzy matching (extracted to fuzzy_match.py)
from fuzzy_match import build_merged_df_enhanced

app = Flask(__name__)
app.secret_key = "supersecret-deep-water"

##############################################################################
# Combine both dictionaries for route usage
##############################################################################

SOURCES_DICT = {
    "otoparts": AVAILABLE_BRANDS_MODELS_OTOPARTS,
    "autopia":  AVAILABLE_BRANDS_MODELS_AUTOPIA
}

##############################################################################
# Globals - Store data in memory
##############################################################################

SCRAPED_DF = pd.DataFrame()
MERGED_DF = pd.DataFrame()

##############################################################################
# Scraping Functions
##############################################################################

def scrape_otoparts(links_list):
    """
    Scrape from otoparts.ge, returning DF with:
      [ProductCode, ProductName, Price, Category, Availability, ImageURL].
    ProductCode is blank.
    """
    all_data = []
    for link in links_list:
        page_number = 1
        while True:
            url = link if page_number == 1 else f"{link}page/{page_number}/"
            print(f"[OtoParts] Scraping: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"Received {resp.status_code}, stopping pagination.")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            products_ul = soup.find("ul", class_="products")
            if not products_ul:
                print("No <ul class='products'> => end.")
                break

            product_items = products_ul.find_all("li", class_="product")
            if not product_items:
                print("No <li class='product'> => end.")
                break

            for li in product_items:
                title_tag = li.find("h2", class_="woocommerce-loop-product__title")
                product_name = title_tag.get_text(strip=True) if title_tag else ""

                price_tag = li.find("span", class_="woocommerce-Price-amount")
                price = price_tag.get_text(strip=True) if price_tag else ""

                cat_span = li.find("span", class_="premium-woo-product-category")
                category = cat_span.get_text(strip=True) if cat_span else ""

                availability = "in stock"
                if "outofstock" in li.get("class", []):
                    availability = "out of stock"

                img_tag = li.find("img")
                img_url = img_tag.get("src", "").strip() if img_tag else ""
                if img_url.startswith("/"):
                    img_url = "https://otoparts.ge" + img_url

                row = {
                    "ProductCode": "",
                    "ProductName": product_name,
                    "Price": price,
                    "Category": category,
                    "Availability": availability,
                    "ImageURL": img_url
                }
                all_data.append(row)

            page_number += 1
    return pd.DataFrame(all_data)


def scrape_autopia(links_list):
    """
    Scrape from autopia.ge, returning DF with:
      [ProductCode, ProductName, Price, Category, Availability, ImageURL].
    Uses pagination guard: if no new product codes appear, we stop.
    """
    all_data = []
    for link in links_list:
        page_number = 1
        previous_codes = set()
        while True:
            url = link if page_number == 1 else f"{link}&page={page_number}"
            print(f"[Autopia] Scraping: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"Received {resp.status_code}, stopping.")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            product_divs = soup.find_all("div", class_="product-layout")
            if not product_divs:
                print("No .product-layout => end.")
                break

            current_page_codes = set()
            new_rows = []
            for div in product_divs:
                right_block = div.find("div", class_="right-block")
                if not right_block:
                    continue
                button = right_block.find("button", class_="addToCart")
                if not button:
                    continue

                product_code = button.get("data-code", "").strip()
                product_name = button.get("data-name", "").strip()
                price_raw    = button.get("data-price", "").strip()
                data_storage = button.get("data-storage", "")
                availability = "out of stock" if data_storage == "0" else "in stock"

                # image from data-img or fallback
                img_url = button.get("data-img", "").strip()
                if not img_url:
                    left_block = div.find("div", class_="left-block")
                    if left_block:
                        img_tag = left_block.find("img")
                        if img_tag:
                            img_url = img_tag.get("src", "").strip()

                if img_url.startswith("/"):
                    img_url = "https://autopia.ge" + img_url

                row = {
                    "ProductCode": product_code,
                    "ProductName": product_name,
                    "Price": (price_raw + "₾") if price_raw else "",
                    "Category": "",
                    "Availability": availability,
                    "ImageURL": img_url
                }
                new_rows.append(row)
                current_page_codes.add(product_code)

            if not new_rows:
                print("No new rows => break")
                break
            if current_page_codes.issubset(previous_codes):
                print("No new product codes => break")
                break

            all_data.extend(new_rows)
            previous_codes |= current_page_codes
            page_number += 1
    return pd.DataFrame(all_data)

##############################################################################
# ROUTES
##############################################################################

@app.route("/", methods=["GET"])
def index():
    # Renders templates/index.html
    return render_template("index.html", scraped_df=SCRAPED_DF)

@app.route("/pick_brand", methods=["POST"])
def pick_brand():
    chosen_source = request.form.get("chosen_source")
    if chosen_source not in SOURCES_DICT:
        return "Invalid source. <a href='/'>Back</a>"

    brand_dict = SOURCES_DICT[chosen_source]
    return render_template("pick_brand.html",
                           chosen_source=chosen_source,
                           brand_dict=brand_dict)

@app.route("/pick_models", methods=["POST"])
def pick_models():
    chosen_source = request.form.get("chosen_source")
    brand = request.form.get("brand")

    if chosen_source not in SOURCES_DICT:
        return "Invalid source. <a href='/'>Back</a>"
    if brand not in SOURCES_DICT[chosen_source]:
        return "Invalid brand. <a href='/'>Back</a>"

    model_map = SOURCES_DICT[chosen_source][brand]
    return render_template("pick_models.html",
                           chosen_source=chosen_source,
                           brand=brand,
                           model_map=model_map)

@app.route("/start_scrape_models", methods=["POST"])
def start_scrape_models():
    global SCRAPED_DF
    chosen_source = request.form.get("chosen_source")
    brand = request.form.get("brand")
    chosen_models = request.form.getlist("models")

    if chosen_source not in SOURCES_DICT:
        return "Invalid source. <a href='/'>Back</a>"
    if brand not in SOURCES_DICT[chosen_source]:
        return "Invalid brand. <a href='/'>Back</a>"
    if not chosen_models:
        return "No models selected. <a href='/'>Back</a>"

    brand_dict = SOURCES_DICT[chosen_source][brand]
    all_dfs = []
    for model_key in chosen_models:
        if model_key not in brand_dict:
            continue
        link = brand_dict[model_key]

        if chosen_source == "otoparts":
            df_one = scrape_otoparts([link])
        else:
            df_one = scrape_autopia([link])

        df_one["Category"] = model_key
        all_dfs.append(df_one)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=["ProductCode","ProductName","Price","Category","Availability","ImageURL"])

    SCRAPED_DF = combined
    return redirect(url_for("index"))

@app.route("/upload_internal", methods=["POST"])
def upload_internal():
    from fuzzy_match import build_merged_df_enhanced  # or top-level import, your choice
    global SCRAPED_DF, MERGED_DF

    if SCRAPED_DF.empty:
        return "No scraped data. <a href='/'>Back</a>"

    file = request.files.get("internal_csv")
    if not file:
        return "No CSV file. <a href='/'>Back</a>"

    threshold_str = request.form.get("threshold", "70")
    try:
        threshold = int(threshold_str)
    except:
        threshold = 70

    try:
        df_internal = pd.read_csv(file)
        required_cols = {"InternalMarkModelYear","InternalDescription"}
        if not required_cols.issubset(df_internal.columns):
            file.seek(0)
            df_internal = pd.read_csv(file, encoding="utf-8-sig")
        if not required_cols.issubset(df_internal.columns):
            file.seek(0)
            df_internal = pd.read_csv(file, encoding="utf-8-sig", sep=";")

        if not required_cols.issubset(df_internal.columns):
            return (f"Missing columns {required_cols}, found {df_internal.columns.tolist()} <a href='/'>Back</a>")
    except Exception as e:
        return f"Error reading CSV: {e} <a href='/'>Back</a>"

    MERGED_DF = build_merged_df_enhanced(df_internal, SCRAPED_DF, threshold=threshold)
    return render_template("results.html", merged_df=MERGED_DF)

@app.route("/download_scraped", methods=["GET"])
def download_scraped():
    global SCRAPED_DF
    if SCRAPED_DF.empty:
        return "No scraped data. <a href='/'>Back</a>"

    buffer = io.StringIO()
    SCRAPED_DF.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="scraped_result.csv",
        mimetype="text/csv"
    )

@app.route("/download_merged", methods=["GET"])
def download_merged():
    global MERGED_DF
    if MERGED_DF.empty:
        return "No merged data. <a href='/'>Back</a>"

    buffer = io.StringIO()
    MERGED_DF.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="merged_result.csv",
        mimetype="text/csv"
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)
