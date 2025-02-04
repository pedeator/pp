# fuzzy_match.py

import re
import pandas as pd
from thefuzz import fuzz


def parse_years_from_string(text):
    matches = re.findall(r'\b(20\d{2}|19\d{2}|\d{2})\b', text)
    if not matches:
        return None
    found = matches[0]
    if len(found) == 2:
        return 2000 + int(found)
    return int(found)

def parse_model_from_string(text):
    cleaned = re.sub(r'[\d()\-]', ' ', text.lower())
    tokens = cleaned.split()
    return max(tokens, key=len) if tokens else ""

def parse_category(category_text):
    cat = category_text.lower()
    # pattern: "20xx - 20xx" or "xx - xx"
    match = re.search(r'(\b20\d{2}\b|\b\d{2}\b)\s*-\s*(\b20\d{2}\b|\b\d{2}\b)', cat)
    if match:
        g1, g2 = match.groups()
        start = int(g1) if len(g1) == 4 else 2000 + int(g1)
        end   = int(g2) if len(g2) == 4 else 2000 + int(g2)
        leftover = cat.replace(match.group(0), '')
        leftover = re.sub(r'[^a-z]', ' ', leftover)
        tokens = leftover.split()
        model = max(tokens, key=len) if tokens else cat
        return model.strip(), start, end

    # pattern: "20xx on" or "xx on"
    match2 = re.search(r'(\b20\d{2}\b|\b\d{2}\b)\s*on', cat)
    if match2:
        g1 = match2.group(1)
        start = int(g1) if len(g1) == 4 else 2000 + int(g1)
        end = 9999
        leftover = cat.replace(match2.group(0), '')
        leftover = re.sub(r'[^a-z]', ' ', leftover)
        tokens = leftover.split()
        model = max(tokens, key=len) if tokens else cat
        return model.strip(), start, end

    leftover = re.sub(r'[^a-z]', ' ', cat)
    tokens = leftover.split()
    model = max(tokens, key=len) if tokens else cat
    return model.strip(), None, None

def is_year_in_range(year, start, end):
    if year is None:
        return True
    if start is not None and year < start:
        return False
    if end is not None and year > end:
        return False
    return True

def build_merged_df_enhanced(df_internal, df_scrapped, threshold=70):
    """
    df_internal => must have [InternalMarkModelYear, InternalDescription]
    df_scrapped => [ProductCode, ProductName, Price, Category, Availability, ImageURL]
    
    Returns a DF with columns:
      [InternalMarkModelYear, InternalDescription, OtoPartsProductName,
       OtoPartsCategory, OtoPartsPrice, OtoPartsImageURL]
    """
    if df_scrapped.empty:
        return pd.DataFrame(columns=[
            "InternalMarkModelYear","InternalDescription",
            "OtoPartsProductName","OtoPartsCategory","OtoPartsPrice","OtoPartsImageURL"
        ])

    # Parse categories
    unique_cats = df_scrapped["Category"].unique()
    cat_info = []
    for c in unique_cats:
        pm, ys, ye = parse_category(c)
        cat_info.append({
            "original_category": c,
            "parsed_model": pm,
            "start": ys,
            "end": ye
        })
    cat_info_df = pd.DataFrame(cat_info)

    output_rows = []
    for _, irow in df_internal.iterrows():
        mm_year = str(irow["InternalMarkModelYear"])
        desc    = str(irow["InternalDescription"])

        user_year  = parse_years_from_string(mm_year)
        user_model = parse_model_from_string(mm_year)

        # Filter cat_info_df to those in range
        possible = cat_info_df[cat_info_df.apply(
            lambda x: is_year_in_range(user_year, x["start"], x["end"]),
            axis=1
        )]
        # fallback if none match
        if possible.empty:
            possible = cat_info_df

        # fuzzy match user_model to cinfo["parsed_model"]
        best_cat = None
        best_cat_score = 0
        for _, cinfo in possible.iterrows():
            sc = fuzz.token_set_ratio(user_model, cinfo["parsed_model"])
            if sc > best_cat_score:
                best_cat_score = sc
                best_cat = cinfo["original_category"]

        if best_cat and best_cat_score >= threshold:
            # filter scrapped to that cat
            subset = df_scrapped[df_scrapped["Category"] == best_cat]
            if subset.empty:
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": "",
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": "",
                    "OtoPartsImageURL": ""
                })
                continue

            # within that subset, fuzzy match desc -> ProductName
            best_prod_score = 0
            best_pname      = ""
            best_price      = ""
            best_img        = ""
            for _, prow in subset.iterrows():
                candidate_name = prow["ProductName"]
                pr = prow["Price"]
                img = prow["ImageURL"]
                scp = fuzz.token_set_ratio(desc, candidate_name)
                if scp > best_prod_score:
                    best_prod_score = scp
                    best_pname = candidate_name
                    best_price = pr
                    best_img   = img

            if best_prod_score >= threshold:
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": best_pname,
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": best_price,
                    "OtoPartsImageURL": best_img
                })
            else:
                # cat matched but no product above threshold
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": "",
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": "",
                    "OtoPartsImageURL": ""
                })
        else:
            # no cat above threshold
            output_rows.append({
                "InternalMarkModelYear": mm_year,
                "InternalDescription": desc,
                "OtoPartsProductName": "",
                "OtoPartsCategory": "",
                "OtoPartsPrice": "",
                "OtoPartsImageURL": ""
            })

    return pd.DataFrame(output_rows)
