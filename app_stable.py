# app.py

import os
import re
import io
import requests
import pandas as pd
from flask import Flask, render_template_string, request, send_file, redirect, url_for
from bs4 import BeautifulSoup
from thefuzz import fuzz, process

##############################################################################
#  FLASK APP SETUP
##############################################################################

app = Flask(__name__)
app.secret_key = "supersecret-deep-water"

##############################################################################
#  GLOBALS - FULL DICTIONARIES
##############################################################################

# ---------------------- OTOPARTS DICTIONARY ---------------------- #
AVAILABLE_BRANDS_MODELS_OTOPARTS = {
    "Ford": {
        "focus-2011-2015": "https://otoparts.ge/product-category/ford/focus-2011-2015/",
        "focus-2012-2015": "https://otoparts.ge/product-category/ford/focus-2012-2015/",
        "focus-15-16":     "https://otoparts.ge/product-category/ford/focus-15-16/",
        "mustang-2010-2012":"https://otoparts.ge/product-category/ford/mustang-2010-2012/",
        "mustang-2015-2017":"https://otoparts.ge/product-category/ford/mustang-2015-2017/",
        "fusion-13-16":    "https://otoparts.ge/product-category/ford/fusion-13-16/",
        "fusion-16-18":    "https://otoparts.ge/product-category/ford/fusion-16-18/",
        "fusion-2019-on":  "https://otoparts.ge/product-category/ford/fusion-2019-on/",
        "fiesta-11-17":    "https://otoparts.ge/product-category/ford/fiesta-11-17/",
        "ecosport-2018-2023":"https://otoparts.ge/product-category/ford/ecosport-2018-2023/",
        "escape-2017-2019":"https://otoparts.ge/product-category/ford/escape-2017-2019/",
        "escape-2020-2023":"https://otoparts.ge/product-category/ford/escape-2020-2023/",
        "explorer-2016-2019":"https://otoparts.ge/product-category/ford/explorer-2016-2019/",
        "explorer-2020-on":"https://otoparts.ge/product-category/ford/explorer-2020-on/"
    },
    "Audi": {
        "a4-2007-2011": "https://otoparts.ge/product-category/audi/a4-2007-2011/",
        "a4-2013-2015": "https://otoparts.ge/product-category/audi/a4-2013-2015/",
        "a4-2016-2018": "https://otoparts.ge/product-category/audi/a4-2016-2018/",
        "a4-2020-on":   "https://otoparts.ge/product-category/audi/a4-2020-on/",
        "a5-2013-2017": "https://otoparts.ge/product-category/audi/a5-2013-2017/",
        "a5-2017-2019": "https://otoparts.ge/product-category/audi/a5-2017-2019/",
        "a6-2008-2010": "https://otoparts.ge/product-category/audi/a6-2008-2010/",
        "a6-2013-2015": "https://otoparts.ge/product-category/audi/a6-2013-2015/",
        "a6-2016-2018": "https://otoparts.ge/product-category/audi/a6-2016-2018/",
        "a7-2011-2015": "https://otoparts.ge/product-category/audi/a7-2011-2015/",
        "a7-2016-2018": "https://otoparts.ge/product-category/audi/a7-2016-2018/",
        "q3-2014-2018": "https://otoparts.ge/product-category/audi/q3-2014-2018/",
        "q5-2008-2012": "https://otoparts.ge/product-category/audi/q5-2008-2012/",
        "q5-2013-on":   "https://otoparts.ge/product-category/audi/q5-2013-on/",
        "q5-2017-2020":"https://otoparts.ge/product-category/audi/q5-2017-2020/",
        "q7-2009-2015": "https://otoparts.ge/product-category/audi/q7-2009-2015/",
        "q7-2016-2019": "https://otoparts.ge/product-category/audi/q7-2016-2019/"
    },
    "BMW": {
        "3-series-f30-2015-2018": "https://otoparts.ge/product-category/bmw/3-series-f30-2015-2018/",
        "3-series-e46-2002-2005": "https://otoparts.ge/product-category/bmw/3-series-e46-2002-2005/",
        "3-series-2008-2013":     "https://otoparts.ge/product-category/bmw/3-series-2008-2013/",
        "3-series-f30-2012-2015": "https://otoparts.ge/product-category/bmw/3-series-f30-2012-2015/",
        "3-series-g-20-2019-2021":"https://otoparts.ge/product-category/bmw/3-series-g-20-2019-2021/",
        "4-series-f32-2014-2017": "https://otoparts.ge/product-category/bmw/4-series-f32-2014-2017/",
        "5-series-f10-2010-2013": "https://otoparts.ge/product-category/bmw/5-series-f10-2010-2013/",
        "5-series-f10-2014-2017": "https://otoparts.ge/product-category/bmw/5-series-f10-2014-2017/",
        "5-series-2017-on":       "https://otoparts.ge/product-category/bmw/5-series-2017-on/",
        "x5-e70-2007-2010":       "https://otoparts.ge/product-category/bmw/x5-e70-2007-2010/",
        "x5-e70-2011-2013":       "https://otoparts.ge/product-category/bmw/x5-e70-2011-2013/",
        "x5-f15-2014-2018":       "https://otoparts.ge/product-category/bmw/x5-f15-2014-2018/",
        "x5-g05-2019-2023":       "https://otoparts.ge/product-category/bmw/x5-g05-2019-2023/",
        "x6-e71-2007-2013":       "https://otoparts.ge/product-category/bmw/x6-e71-2007-2013/"
    },
    "Chevrolet": {
        "camaro-2008-2013": "https://otoparts.ge/product-category/chevrolet/camaro-2008-2013/",
        "camaro-2014-2015": "https://otoparts.ge/product-category/chevrolet/camaro-2014-2015/",
        "cruze-2011-2015":  "https://otoparts.ge/product-category/chevrolet/cruze-2011-2015/",
        "cruze-2016-2019":  "https://otoparts.ge/product-category/chevrolet/cruze-2016-2019/",
        "cruze-2019":       "https://otoparts.ge/product-category/chevrolet/cruze-2019/",
        "malibu-2013-2015": "https://otoparts.ge/product-category/chevrolet/malibu-2013-2015/",
        "malibu-2015-on":   "https://otoparts.ge/product-category/chevrolet/malibu-2015-on/",
        "malibu-2019":      "https://otoparts.ge/product-category/chevrolet/malibu-2019/",
        "trax-2017-2021":   "https://otoparts.ge/product-category/chevrolet/trax-2017-2021/",
        "equinox-2017-2021":"https://otoparts.ge/product-category/chevrolet/equinox-2017-2021/"
    },
    "Fiat": {
        "500-2007-2014": "https://otoparts.ge/product-category/fiat/500-2007-2014/"
    },
    "Honda": {
        "accord-2018-2020": "https://otoparts.ge/product-category/honda/accord-2018-2020/",
        "accord-2020-2022": "https://otoparts.ge/product-category/honda/accord-2020-2022/",
        "civic-2011-2013":  "https://otoparts.ge/product-category/honda/civic-2011-2013/",
        "civic-2012-2015":  "https://otoparts.ge/product-category/honda/civic-2012-2015/",
        "civic-2016-on":    "https://otoparts.ge/product-category/honda/civic-2016-on/",
        "cr-v-2012-2015":   "https://otoparts.ge/product-category/honda/cr-v-2012-2015/",
        "cr-v-2017-2019":   "https://otoparts.ge/product-category/honda/cr-v-2017-2019/",
        "cr-v-2020-2024":   "https://otoparts.ge/product-category/honda/cr-v-2020-2024/",
        "hr-v-2016-2020":   "https://otoparts.ge/product-category/honda/hr-v-2016-2020/",
        "insight-2011-2015":"https://otoparts.ge/product-category/honda/insight-2011-2015/",
        "fit-2008-2014":    "https://otoparts.ge/product-category/honda/fit-2008-2014/",
        "fit-2014-on":      "https://otoparts.ge/product-category/honda/fit-2014-on/"
    },
    "Hyundai": {
        "accent-2011-2015":         "https://otoparts.ge/product-category/hyundai/accent-2011-2015/",
        "accent-2016-on":           "https://otoparts.ge/product-category/hyundai/accent-2016-on/",
        "elantra-2011-2013":        "https://otoparts.ge/product-category/hyundai/elantra-2011-2013/",
        "elantra-2014-2015":        "https://otoparts.ge/product-category/hyundai/elantra-2014-2015/",
        "elantra-2015-on":          "https://otoparts.ge/product-category/hyundai/elantra-2015-on/",
        "elantra-2019":             "https://otoparts.ge/product-category/hyundai/elantra-2019/",
        "elantra-2021-2022":        "https://otoparts.ge/product-category/hyundai/elantra-2021-2022/",
        "elantra-gt-2011-2017":     "https://otoparts.ge/product-category/hyundai/elantra-gt-2011-2017/",
        "ix-35-2010-2015":          "https://otoparts.ge/product-category/hyundai/ix-35-2010-2015/",
        "ix-35-2015-on":            "https://otoparts.ge/product-category/hyundai/ix-35-2015-on/",
        "tucson-2019-2021":         "https://otoparts.ge/product-category/hyundai/tucson-2019-2021/",
        "tucson-2022-on":           "https://otoparts.ge/product-category/hyundai/tucson-2022-on/",
        "santa-fe-2012-2015":       "https://otoparts.ge/product-category/hyundai/santa-fe-2012-2015/",
        "santa-fe-2016-2018":       "https://otoparts.ge/product-category/hyundai/santa-fe-2016-2018/",
        "santa-fe-2019-2021":       "https://otoparts.ge/product-category/hyundai/santa-fe-2019-2021/",
        "sonata-2010-2012":         "https://otoparts.ge/product-category/hyundai/sonata-2010-2012/",
        "sonata-2013-2014-facelift":"https://otoparts.ge/product-category/hyundai/sonata-2013-2014-facelift/",
        "sonata-2014-on":           "https://otoparts.ge/product-category/hyundai/sonata-2014-on/",
        "sonata-2018-2019":         "https://otoparts.ge/product-category/hyundai/sonata-2018-2019/",
        "sonata-2020-2022":         "https://otoparts.ge/product-category/hyundai/sonata-2020-2022/",
        "veloster-2011-on":         "https://otoparts.ge/product-category/hyundai/veloster-2011-on/",
        "kona-2018-2021":           "https://otoparts.ge/product-category/hyundai/kona-2018-2021/",
        "palisade-2020-on":         "https://otoparts.ge/product-category/hyundai/palisade-2020-on/"
    },
    "Kia": {
        "optima-2010-2013":   "https://otoparts.ge/product-category/kia/optima-2010-2013/",
        "optima-2013-2016":   "https://otoparts.ge/product-category/kia/optima-2013-2016/",
        "optima-2016-on":     "https://otoparts.ge/product-category/kia/optima-2016-on/",
        "optima-2018-2019":   "https://otoparts.ge/product-category/kia/optima-2018-2019/",
        "optima-k5-2020-2023":"https://otoparts.ge/product-category/kia/optima-k5-2020-2023/",
        "picanto-2011-2015":  "https://otoparts.ge/product-category/kia/picanto-2011-2015/",
        "picanto-2015-on":    "https://otoparts.ge/product-category/kia/picanto-2015-on/",
        "sportage-2010-2014": "https://otoparts.ge/product-category/kia/sportage-2010-2014/",
        "sportage-2016-2019": "https://otoparts.ge/product-category/kia/sportage-2016-2019/",
        "soul-2008-2014":     "https://otoparts.ge/product-category/kia/soul-2008-2014/"
    },
    "Lexus": {
        "ct-200h-2012-2014":         "https://otoparts.ge/product-category/lexus/ct-200h-2012-2014/",
        "ct-200h-f-sport-2015-on":   "https://otoparts.ge/product-category/lexus/ct-200h-f-sport-2015-on/",
        "ct-200h-2018":              "https://otoparts.ge/product-category/lexus/ct-200h-2018/",
        "es-2012-2015":              "https://otoparts.ge/product-category/lexus/es-2012-2015/",
        "es-2015-2018":              "https://otoparts.ge/product-category/lexus/es-2015-2018/",
        "es-2018-2020":              "https://otoparts.ge/product-category/lexus/es-2018-2020/",
        "is-250-2014-2016":          "https://otoparts.ge/product-category/lexus/is-250-2014-2016/",
        "is-2017-2018":              "https://otoparts.ge/product-category/lexus/is-2017-2018/",
        "rx-2012-2015":              "https://otoparts.ge/product-category/lexus/rx-2012-2015/",
        "rx-2016-on":                "https://otoparts.ge/product-category/lexus/rx-2016-on/",
        "rx-2019-2021":              "https://otoparts.ge/product-category/lexus/rx-2019-2021/",
        "nx-200-2014-on":            "https://otoparts.ge/product-category/lexus/nx-200-2014-on/",
        "nx-2017-2020":              "https://otoparts.ge/product-category/lexus/nx-2017-2020/",
        "hs-2012-on":                "https://otoparts.ge/product-category/lexus/hs-2012-on/"
    },
    "Mazda": {
        "mazda-3-2014-2016": "https://otoparts.ge/product-category/mazda/mazda-3-2014-2016/",
        "mazda-3-2017-2018": "https://otoparts.ge/product-category/mazda/mazda-3-2017-2018/",
        "mazda-3-2019-2022": "https://otoparts.ge/product-category/mazda/mazda-3-2019-2022/",
        "mazda-6-14-16":     "https://otoparts.ge/product-category/mazda/mazda-6-14-16/",
        "mazda-6-2017-2019": "https://otoparts.ge/product-category/mazda/mazda-6-2017-2019/",
        "mazda-6-2020-2022": "https://otoparts.ge/product-category/mazda/mazda-6-2020-2022/",
        "cx-5-2014-2016":    "https://otoparts.ge/product-category/mazda/cx-5-2014-2016/",
        "mazda-cx5-2017-2022":"https://otoparts.ge/product-category/mazda/mazda-cx5-2017-2022/",
        "mazda-cx5-2022-on": "https://otoparts.ge/product-category/mazda/mazda-cx5-2022-on/"
    },
    "Mercedes-Benz": {
        "c-class-w204-2007-2010":       "https://otoparts.ge/product-category/mercedes-benz/c-class-w204-2007-2010/",
        "c-class-w204-2011-2015":       "https://otoparts.ge/product-category/mercedes-benz/c-class-w204-2011-2015/",
        "c-class-w205-2014-on":         "https://otoparts.ge/product-category/mercedes-benz/c-class-w205-2014-on/",
        "cla-c117-2013-2016":           "https://otoparts.ge/product-category/mercedes-benz/cla-c117-2013-2016/",
        "cla-c117-2016-2019":           "https://otoparts.ge/product-category/mercedes-benz/cla-c117-2016-2019/",
        "cls-w218-2013-2016":           "https://otoparts.ge/product-category/mercedes-benz/cls-w218-2013-2016/",
        "e-class-w212-2009-2013":       "https://otoparts.ge/product-category/mercedes-benz/e-class-w212-2009-2013/",
        "e-class-w212-2013-2016":       "https://otoparts.ge/product-category/mercedes-benz/e-class-w212-2013-2016/",
        "e-2017-2019":                  "https://otoparts.ge/product-category/mercedes-benz/e-2017-2019/",
        "s-221-2007-2013":              "https://otoparts.ge/product-category/mercedes-benz/s-221-2007-2013/",
        "s-2018-2020":                  "https://otoparts.ge/product-category/mercedes-benz/s-2018-2020/",
        "glk-2010-2015":                "https://otoparts.ge/product-category/mercedes-benz/glk-2010-2015/",
        "gla-2014-2016":                "https://otoparts.ge/product-category/mercedes-benz/gla-2014-2016/",
        "gla-2017-2019":                "https://otoparts.ge/product-category/mercedes-benz/gla-2017-2019/",
        "ml-2008-2011":                 "https://otoparts.ge/product-category/mercedes-benz/ml-2008-2011/",
        "ml-w166-2011-2015":            "https://otoparts.ge/product-category/mercedes-benz/ml-w166-2011-2015/",
        "gl-class-x164-2009-2012":      "https://otoparts.ge/product-category/mercedes-benz/gl-class-x164-2009-2012/",
        "x166-2013-2019":               "https://otoparts.ge/product-category/mercedes-benz/x166-2013-2019/",
        "gle-w166-2015-on":             "https://otoparts.ge/product-category/mercedes-benz/gle-w166-2015-on/",
        "gle-gle-coupe-2015-2019":      "https://otoparts.ge/product-category/mercedes-benz/gle-gle-coupe-2015-2019/",
        "glc-2015-2017":                "https://otoparts.ge/product-category/mercedes-benz/glc-2015-2017/",
        "glc-2018-2020":                "https://otoparts.ge/product-category/mercedes-benz/glc-2018-2020/",
        "gls-x167-2020-on":             "https://otoparts.ge/product-category/mercedes-benz/gls-x167-2020-on/",
        "gle-w167-2020-on":             "https://otoparts.ge/product-category/mercedes-benz/gle-w167-2020-on/"
    },
}

# ---------------------- AUTOPIA DICTIONARY ---------------------- #
AVAILABLE_BRANDS_MODELS_AUTOPIA = {
    # BMW brand on autopia
    "BMW": {
        "1 E81/87 2004-2011":    "https://autopia.ge/en/products?mark=3&model=1064",
        "1 F20/F21 2012-2019":   "https://autopia.ge/en/products?mark=3&model=1066",
        "1 F40/F44 2020-2024":   "https://autopia.ge/en/products?mark=3&model=1100",
        "2 F45 2015-":           "https://autopia.ge/en/products?mark=3&model=1068",
        "3 G20 - 2020-":         "https://autopia.ge/en/products?mark=3&model=1081",
        "3 F30/F31 2011-2018":   "https://autopia.ge/en/products?mark=3&model=1239",
        "3 E93 2006-2013":       "https://autopia.ge/en/products?mark=3&model=1078",
        "3 E92 COUPE 2006-2012": "https://autopia.ge/en/products?mark=3&model=1077",
        "3 E90 2005-2009":       "https://autopia.ge/en/products?mark=3&model=1075",
        "3 E36 1990-1999":       "https://autopia.ge/en/products?mark=3&model=1111",
        "3 E36 COUPE 1990-1999":"https://autopia.ge/en/products?mark=3&model=1115",
        "3 E46 1998-2002":       "https://autopia.ge/en/products?mark=3&model=1071",
        "3 E46 2002-2005":       "https://autopia.ge/en/products?mark=3&model=1072",
        "3 E46 COUPE 2001-2003":"https://autopia.ge/en/products?mark=3&model=1073",
        "3 E46 COUPE 2003-2005":"https://autopia.ge/en/products?mark=3&model=1074",
        "3 E90/91 2009-2012":    "https://autopia.ge/en/products?mark=3&model=1076",
        "4 F32 2013-2020":       "https://autopia.ge/en/products?mark=3&model=1083",
        "4 F33 CABRIO 2013-2020":"https://autopia.ge/en/products?mark=3&model=1082",
        "5 E34 1988-1995":       "https://autopia.ge/en/products?mark=3&model=1084",
        "5 E39 1995-2003":       "https://autopia.ge/en/products?mark=3&model=1085",
        "5 E60 2003-2007":       "https://autopia.ge/en/products?mark=3&model=1086",
        "5 E60 2007-2010":       "https://autopia.ge/en/products?mark=3&model=1087",
        "5 GRAND TURISMO F07 2009-2017": "https://autopia.ge/en/products?mark=3&model=1271",
        "5 F10/F11 2010-":       "https://autopia.ge/en/products?mark=3&model=1090",
        "5 G30/G31 2017-2020":   "https://autopia.ge/en/products?mark=3&model=1063",
        "5 G30/G31 2020-":       "https://autopia.ge/en/products?mark=3&model=1089",
        "6 E63 2004-2010":       "https://autopia.ge/en/products?mark=3&model=1092",
        "6 S F12/F13 COUPE/CABRIOLET 2012-": "https://autopia.ge/en/products?mark=3&model=1097",
        "7 S E38 1994-2001":     "https://autopia.ge/en/products?mark=3&model=1093",
        "7 S E65/E66 2002-2008": "https://autopia.ge/en/products?mark=3&model=1091",
        "7 SR 2006-":           "https://autopia.ge/en/products?mark=3&model=328",
        "7 S F01/F02 2008-2012":"https://autopia.ge/en/products?mark=3&model=1094",
        "7 S G11/G12 2016-2018":"https://autopia.ge/en/products?mark=3&model=1095",
        "7 S G11/G12 2019-":    "https://autopia.ge/en/products?mark=3&model=1096",
        "X1 E84 2009-2013":     "https://autopia.ge/en/products?mark=3&model=327",
        "X1 E84 2013-2015":     "https://autopia.ge/en/products?mark=3&model=338",
        "X1 F48 2015-2019":     "https://autopia.ge/en/products?mark=3&model=776",
        "X1 U11 2022-":         "https://autopia.ge/en/products?mark=3&model=1182",
        "X2 F39 2018-":         "https://autopia.ge/en/products?mark=3&model=948",
        "X3 2004-2009":         "https://autopia.ge/en/products?mark=3&model=1268",
        "X3 G01 2018-":         "https://autopia.ge/en/products?mark=3&model=783",
        "X4 F26 2015-":         "https://autopia.ge/en/products?mark=3&model=673",
        "X4 G02 2019-":         "https://autopia.ge/en/products?mark=3&model=1018",
        "X5 E53 2000-2006":     "https://autopia.ge/en/products?mark=3&model=36",
        "X5 E53 2004-":         "https://autopia.ge/en/products?mark=3&model=37",
        "X5 E70 2007-2010":     "https://autopia.ge/en/products?mark=3&model=32",
        "X5 E70 2010-2013":     "https://autopia.ge/en/products?mark=3&model=40",
        "X5 F15 2014-":         "https://autopia.ge/en/products?mark=3&model=326",
        "X5 G05 2019-":         "https://autopia.ge/en/products?mark=3&model=786",
        "X6 E71 2008-":         "https://autopia.ge/en/products?mark=3&model=402",
        "X6 F16 2015-":         "https://autopia.ge/en/products?mark=3&model=461",
        "X6 G06 2020-":         "https://autopia.ge/en/products?mark=3&model=743",
        "X7 G07 2019-":         "https://autopia.ge/en/products?mark=3&model=865",
        "I3 2013-":             "https://autopia.ge/en/products?mark=3&model=578",
        "I8 2014-":             "https://autopia.ge/en/products?mark=3&model=1199",
        "Z4 E85 2003-2009":     "https://autopia.ge/en/products?mark=3&model=442",
        "Z4 E86 COUPE 2006-":   "https://autopia.ge/en/products?mark=3&model=1098",
        "Z4 E89 CABRIO 2009-":  "https://autopia.ge/en/products?mark=3&model=1099",
        "5 S G60/G61 2024-":    "https://autopia.ge/en/products?mark=3&model=1350",
        "X1 F48 2020-":         "https://autopia.ge/en/products?mark=3&model=1351",
        "X3 F25 2014-2017":     "https://autopia.ge/en/products?mark=3&model=1352",
        "3 S G20 M SPORT 2020-2022": "https://autopia.ge/en/products?mark=3&model=1353",
        "X3 F25 2010-2014":     "https://autopia.ge/en/products?mark=3&model=1354",
        "7 S G11/G12 M SPORT 2016-2018": "https://autopia.ge/en/products?mark=3&model=1356",
        "7 S F02 2012-2015":    "https://autopia.ge/en/products?mark=3&model=1358",
        "3 G20 - 2020-":        "https://autopia.ge/en/products?mark=3&model=1386",
        "X3 F25 2010-2017":     "https://autopia.ge/en/products?mark=3&model=1387",
        "8 S G16 2019-":        "https://autopia.ge/en/products?mark=3&model=1402"
    },
    # Buick
    "Buick": {
        "ENCORE 2013-2016":   "https://autopia.ge/en/products?mark=68&model=1179",
        "ENCORE 2017-2021":   "https://autopia.ge/en/products?mark=68&model=1159",
        "ENCORE GX 2021-":    "https://autopia.ge/en/products?mark=68&model=1180",
        "ENVISION 2021-":     "https://autopia.ge/en/products?mark=68&model=1181"
    },
    # Cadillac
    "Cadillac": {
        "ESCALADE 2015-":     "https://autopia.ge/en/products?mark=78&model=1218",
        "ESCALADE 2021-":     "https://autopia.ge/en/products?mark=78&model=995",
        "CTS 4D SEDAN 2014-": "https://autopia.ge/en/products?mark=78&model=965",
        "SRX 2010-":          "https://autopia.ge/en/products?mark=78&model=1035",
        "ATS 2013-2019":      "https://autopia.ge/en/products?mark=78&model=1272",
        "CTS 2014-":          "https://autopia.ge/en/products?mark=78&model=1273",
        "XT4 2019-":          "https://autopia.ge/en/products?mark=78&model=1274"
    },
    # Chevrolet
    "Chevrolet": {
        "CRUZE 2013-2015":    "https://autopia.ge/en/products?mark=12&model=41",
        "CRUZE 2016-2020":    "https://autopia.ge/en/products?mark=12&model=42",
        "MALIBU 2013-":       "https://autopia.ge/en/products?mark=12&model=287",
        "MALIBU 2016-2023":   "https://autopia.ge/en/products?mark=12&model=269",
        "MALIBU 2019-":       "https://autopia.ge/en/products?mark=12&model=453",
        "CAMARO 2D COUPE 2010-": "https://autopia.ge/en/products?mark=12&model=270",
        "CAMARO 2016-":           "https://autopia.ge/en/products?mark=12&model=698",
        "VOLT H/B 2011-":         "https://autopia.ge/en/products?mark=12&model=400",
        "VOLT 2016-":             "https://autopia.ge/en/products?mark=12&model=456",
        "BOLT 2022-":             "https://autopia.ge/en/products?mark=12&model=1052",
        "EQUINOX 2010-2015":      "https://autopia.ge/en/products?mark=12&model=427",
        "EQUINOX 2018-2021":      "https://autopia.ge/en/products?mark=12&model=748",
        "TRAX 2014-2016":         "https://autopia.ge/en/products?mark=12&model=521",
        "TRAX 2017-":             "https://autopia.ge/en/products?mark=12&model=463",
        "CAPTIVA 2006-":          "https://autopia.ge/en/products?mark=12&model=401",
        "SPARK 2017-":            "https://autopia.ge/en/products?mark=12&model=740",
        "SUBURBAN TAHOE 07-14 /YUKON/ESCALADE/SILVERADO": "https://autopia.ge/en/products?mark=12&model=967",
        "AVEO (T300)/SONIC SEDAN/HATCHBACK 2011-":        "https://autopia.ge/en/products?mark=12&model=968",
        "BLAZER 2019-":           "https://autopia.ge/en/products?mark=12&model=969",
        "TRAILBLAZER 5D SUV 2019-": "https://autopia.ge/en/products?mark=12&model=971",
        "ORLANDO 2011-":          "https://autopia.ge/en/products?mark=12&model=970",
        "SONIC 2012-":            "https://autopia.ge/en/products?mark=12&model=1382",
        "CHEV CORVETTE C7 COUPE/CABRIOLET 2014-19": "https://autopia.ge/en/products?mark=12&model=1403",
        "CHEV SILVERADO SIERRA 2019-":             "https://autopia.ge/en/products?mark=12&model=1404",
        "CORVETTE 2D COUPE 1973-77":               "https://autopia.ge/en/products?mark=12&model=1405",
        "CAPTIVA 2011-":                           "https://autopia.ge/en/products?mark=12&model=1417"
    }
}

# We'll unify them under a top-level dict that references OtoParts vs. Autopia
SOURCES_DICT = {
    "otoparts": AVAILABLE_BRANDS_MODELS_OTOPARTS,
    "autopia":  AVAILABLE_BRANDS_MODELS_AUTOPIA
}

# Our global DataFrames
SCRAPED_DF = pd.DataFrame()
MERGED_DF = pd.DataFrame()

##############################################################################
#  OTOPARTS SCRAPER
##############################################################################

def scrape_otoparts(links_list):
    """
    Scrapes otoparts.ge product pages.
    Returns DataFrame columns: [ProductCode, ProductName, Price, Category, Availability].
    ProductCode is blank for OtoParts.
    """
    all_data = []
    for link in links_list:
        page_number = 1
        while True:
            if page_number == 1:
                url = link
            else:
                url = f"{link}page/{page_number}/"

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
                # ProductName
                title_tag = li.find("h2", class_="woocommerce-loop-product__title")
                product_name = title_tag.get_text(strip=True) if title_tag else ""

                # Price
                price_tag = li.find("span", class_="woocommerce-Price-amount")
                price = price_tag.get_text(strip=True) if price_tag else ""

                # Category
                cat_span = li.find("span", class_="premium-woo-product-category")
                category = cat_span.get_text(strip=True) if cat_span else ""

                # Availability
                availability = "in stock"
                if "outofstock" in li.get("class", []):
                    availability = "out of stock"

                row = {
                    "ProductCode": "",
                    "ProductName": product_name,
                    "Price": price,
                    "Category": category,
                    "Availability": availability
                }
                all_data.append(row)
            page_number += 1

    return pd.DataFrame(all_data)

##############################################################################
#  AUTOPIA SCRAPER (with infinite-page guard)
##############################################################################

def scrape_autopia(links_list):
    """
    Scrapes autopia.ge product pages with a guard to avoid infinite pagination.
    We compare product codes each page; if no new codes appear, we break.
    Returns DF columns: [ProductCode, ProductName, Price, Category, Availability].
    """
    all_data = []
    for link in links_list:
        page_number = 1
        previous_codes = set()

        while True:
            if page_number == 1:
                url = link
            else:
                url = f"{link}&page={page_number}"

            print(f"[Autopia] Scraping: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"Received {resp.status_code}, stopping.")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            product_divs = soup.find_all("div", class_="product-layout")

            if not product_divs:
                print("No .product-layout => likely end.")
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

                availability = "in stock"
                if data_storage == "0":
                    availability = "out of stock"

                row = {
                    "ProductCode": product_code,
                    "ProductName": product_name,
                    "Price": (price_raw + "₾") if price_raw else "",
                    "Category": "",  # We'll set real category after
                    "Availability": availability
                }
                new_rows.append(row)
                current_page_codes.add(product_code)

            if not new_rows:
                print("No new rows => break")
                break

            # If we see no new codes vs. previous, break to avoid infinite loop
            if current_page_codes.issubset(previous_codes):
                print("No new product codes => break")
                break

            # otherwise add them to all_data
            for r in new_rows:
                all_data.append(r)

            previous_codes = previous_codes.union(current_page_codes)
            page_number += 1

    return pd.DataFrame(all_data)

##############################################################################
#  FUZZY MATCH UTILITIES
##############################################################################

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
    if not tokens:
        return ""
    return max(tokens, key=len)

def parse_category(category_text):
    cat = category_text.lower()
    # pattern: "13-16" or "2013-2016"
    match = re.search(r'(\b20\d{2}\b|\b\d{2}\b)\s*-\s*(\b20\d{2}\b|\b\d{2}\b)', cat)
    if match:
        g1, g2 = match.groups()
        start = int(g1) if len(g1) == 4 else 2000 + int(g1)
        end   = int(g2) if len(g2) == 4 else 2000 + int(g2)
        leftover = cat.replace(match.group(0), '')
        leftover = re.sub(r'[^a-z]', ' ', leftover)
        tokens = leftover.split()
        if tokens:
            model = max(tokens, key=len)
        else:
            model = cat
        return model.strip(), start, end

    # pattern: "2019 on"
    match2 = re.search(r'(\b20\d{2}\b|\b\d{2}\b)\s*on', cat)
    if match2:
        g1 = match2.group(1)
        start = int(g1) if len(g1) == 4 else 2000 + int(g1)
        end = 9999
        leftover = cat.replace(match2.group(0), '')
        leftover = re.sub(r'[^a-z]', ' ', leftover)
        tokens = leftover.split()
        if tokens:
            model = max(tokens, key=len)
        else:
            model = cat
        return model.strip(), start, end

    # fallback
    leftover = re.sub(r'[^a-z]', ' ', cat)
    tokens = leftover.split()
    if tokens:
        model = max(tokens, key=len)
    else:
        model = cat
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
    Merges df_internal w/ columns:
      [InternalMarkModelYear, InternalDescription]
    against df_scrapped w/ columns:
      [ProductCode, ProductName, Price, Category, Availability].
    """
    if df_scrapped.empty:
        return pd.DataFrame(columns=[
            "InternalMarkModelYear","InternalDescription",
            "OtoPartsProductName","OtoPartsCategory","OtoPartsPrice"
        ])

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

        possible = cat_info_df[cat_info_df.apply(
            lambda x: is_year_in_range(user_year, x["start"], x["end"]),
            axis=1
        )]
        if possible.empty:
            possible = cat_info_df

        best_cat = None
        best_cat_score = 0
        for _, cinfo in possible.iterrows():
            sc = fuzz.token_set_ratio(user_model, cinfo["parsed_model"])
            if sc > best_cat_score:
                best_cat_score = sc
                best_cat = cinfo["original_category"]

        if best_cat and best_cat_score >= threshold:
            subset = df_scrapped[df_scrapped["Category"] == best_cat]
            if subset.empty:
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": "",
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": ""
                })
                continue

            best_pname = ""
            best_price = ""
            best_pscore = 0
            for _, prow in subset.iterrows():
                candidate = prow["ProductName"]
                pr = prow["Price"]
                s = fuzz.token_set_ratio(desc, candidate)
                if s > best_pscore:
                    best_pscore = s
                    best_pname = candidate
                    best_price = pr

            if best_pscore >= threshold:
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": best_pname,
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": best_price
                })
            else:
                output_rows.append({
                    "InternalMarkModelYear": mm_year,
                    "InternalDescription": desc,
                    "OtoPartsProductName": "",
                    "OtoPartsCategory": best_cat,
                    "OtoPartsPrice": ""
                })
        else:
            output_rows.append({
                "InternalMarkModelYear": mm_year,
                "InternalDescription": desc,
                "OtoPartsProductName": "",
                "OtoPartsCategory": "",
                "OtoPartsPrice": ""
            })

    return pd.DataFrame(output_rows)

##############################################################################
#  HTML Templates (fully inlined, nothing omitted)
##############################################################################

index_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Deep Water - Final MVP</title>
</head>
<body>
<h1>Deep Water - Final Build</h1>

<h2>Step 1) Choose Source</h2>
<form method="POST" action="/pick_brand">
  <label>Select source:</label>
  <select name="chosen_source" required>
    <option value="" disabled selected>-- select source --</option>
    <option value="otoparts">OtoParts</option>
    <option value="autopia">Autopia</option>
  </select>
  <button type="submit">Next</button>
</form>

<hr>
<h2>Step 2) Upload CSV for Fuzzy Match (optional)</h2>
<p>Your CSV must have columns: <b>InternalMarkModelYear</b> and <b>InternalDescription</b></p>
<form method="POST" action="/upload_internal" enctype="multipart/form-data">
  <label>File:
    <input type="file" name="internal_csv" accept=".csv" required>
  </label>
  <br><br>
  <label>Fuzzy threshold (1-100, default=70):
    <input type="number" name="threshold" value="70" min="1" max="100">
  </label>
  <br><br>
  <button type="submit">Upload & Fuzzy Match</button>
</form>

<hr>
<h3>Download Current Scraped Data (before matching)</h3>
<p><a href="/download_scraped">Download scraped CSV</a></p>

<hr>
<h3>Scraped Data ({{ scraped_df.shape[0] }} rows)</h3>
{% if scraped_df.empty %}
  <p>No data yet. Please choose a source -> brand -> models and scrape.</p>
{% else %}
  <table border="1" cellpadding="4" cellspacing="0">
    <tr>
      <th>ProductCode</th>
      <th>ProductName</th>
      <th>Price</th>
      <th>Category</th>
      <th>Availability</th>
    </tr>
    {% for idx, row in scraped_df.iterrows() %}
    <tr>
      <td>{{ row['ProductCode'] }}</td>
      <td>{{ row['ProductName'] }}</td>
      <td>{{ row['Price'] }}</td>
      <td>{{ row['Category'] }}</td>
      <td>{{ row['Availability'] }}</td>
    </tr>
    {% endfor %}
  </table>
{% endif %}
</body>
</html>
"""

pick_brand_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Pick Brand</title>
</head>
<body>
<h1>Pick Brand for {{ chosen_source|capitalize }}</h1>
<form method="POST" action="/pick_models">
  <input type="hidden" name="chosen_source" value="{{ chosen_source }}">
  <label>Brand:</label>
  <select name="brand" required>
    <option value="" disabled selected>-- select brand --</option>
    {% for brand_name in brand_dict.keys() %}
      <option value="{{ brand_name }}">{{ brand_name }}</option>
    {% endfor %}
  </select>
  <button type="submit">Next</button>
</form>
<br>
<a href="/">Back Home</a>
</body>
</html>
"""

pick_models_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Pick Models for {{ brand }} at {{ chosen_source|capitalize }}</title>
</head>
<body>
<h2>Pick Models for {{ brand }} ({{ chosen_source|capitalize }})</h2>
<p>Select which model pages to scrape:</p>
<form method="POST" action="/start_scrape_models">
  <input type="hidden" name="chosen_source" value="{{ chosen_source }}">
  <input type="hidden" name="brand" value="{{ brand }}">
  
  {% for model_key, link in model_map.items() %}
    <label>
      <input type="checkbox" name="models" value="{{ model_key }}">
      {{ model_key }}
    </label><br>
  {% endfor %}
  <br>
  <button type="submit">Scrape</button>
</form>
<br>
<a href="/">Back Home</a>
</body>
</html>
"""

results_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Fuzzy Merge Results</title>
</head>
<body>
<h1>Fuzzy Merge Results</h1>
<p><a href="/download_merged">Download the merged_result.csv</a></p>
<table border="1" cellpadding="4" cellspacing="0">
  <tr>
    <th>InternalMarkModelYear</th>
    <th>InternalDescription</th>
    <th>OtoPartsProductName</th>
    <th>OtoPartsCategory</th>
    <th>OtoPartsPrice</th>
  </tr>
  {% for idx, row in merged_df.iterrows() %}
  <tr>
    <td>{{ row['InternalMarkModelYear'] }}</td>
    <td>{{ row['InternalDescription'] }}</td>
    <td>{{ row['OtoPartsProductName'] }}</td>
    <td>{{ row['OtoPartsCategory'] }}</td>
    <td>{{ row['OtoPartsPrice'] }}</td>
  </tr>
  {% endfor %}
</table>
<br>
<a href="/">Back Home</a>
</body>
</html>
"""

##############################################################################
#  ROUTES
##############################################################################

@app.route("/", methods=["GET"])
def index():
    """ Main page: pick source, optionally do fuzzy match, download. """
    return render_template_string(index_template, scraped_df=SCRAPED_DF)

@app.route("/pick_brand", methods=["POST"])
def pick_brand():
    """ 
    After user selects "chosen_source" (otoparts or autopia), let them choose a brand.
    """
    chosen_source = request.form.get("chosen_source")
    if chosen_source not in SOURCES_DICT:
        return "Invalid source. <a href='/'>Back</a>"

    brand_dict = SOURCES_DICT[chosen_source]
    return render_template_string(
        pick_brand_template,
        chosen_source=chosen_source,
        brand_dict=brand_dict
    )

@app.route("/pick_models", methods=["POST"])
def pick_models():
    """ 
    User picks brand; show all models for that brand in the chosen source dictionary.
    """
    chosen_source = request.form.get("chosen_source")
    brand = request.form.get("brand")

    if chosen_source not in SOURCES_DICT:
        return "Invalid source. <a href='/'>Back</a>"

    if brand not in SOURCES_DICT[chosen_source]:
        return "Invalid brand. <a href='/'>Back</a>"

    model_map = SOURCES_DICT[chosen_source][brand]
    return render_template_string(
        pick_models_template,
        chosen_source=chosen_source,
        brand=brand,
        model_map=model_map
    )

@app.route("/start_scrape_models", methods=["POST"])
def start_scrape_models():
    """
    Actually scrape whichever model pages the user selected. 
    We'll unify them into SCRAPED_DF.
    """
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
    all_rows = []
    for model_key in chosen_models:
        if model_key not in brand_dict:
            continue
        url = brand_dict[model_key]
        if chosen_source == "otoparts":
            single_df = scrape_otoparts([url])
        else:
            single_df = scrape_autopia([url])

        # override final 'Category' with the model_key
        single_df["Category"] = model_key
        all_rows.append(single_df)

    if all_rows:
        combined = pd.concat(all_rows, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=["ProductCode","ProductName","Price","Category","Availability"])

    SCRAPED_DF = combined
    return redirect(url_for("index"))

@app.route("/upload_internal", methods=["POST"])
def upload_internal():
    """
    User uploads CSV with [InternalMarkModelYear, InternalDescription],
    we do fuzzy matching vs. SCRAPED_DF.
    """
    global SCRAPED_DF, MERGED_DF

    if SCRAPED_DF.empty:
        return "No scraped data. Please scrape first. <a href='/'>Back</a>"

    file = request.files.get("internal_csv")
    if not file:
        return "No CSV provided. <a href='/'>Back</a>"

    threshold_str = request.form.get("threshold", "70")
    try:
        threshold = int(threshold_str)
    except:
        threshold = 70

    try:
        df_internal = pd.read_csv(file)
        required_cols = {"InternalMarkModelYear","InternalDescription"}
        if not required_cols.issubset(df_internal.columns):
            # try BOM removal
            file.seek(0)
            df_internal = pd.read_csv(file, encoding="utf-8-sig")
        if not required_cols.issubset(df_internal.columns):
            # try semicolon
            file.seek(0)
            df_internal = pd.read_csv(file, encoding="utf-8-sig", sep=";")

        if not required_cols.issubset(df_internal.columns):
            return (f"Missing columns {required_cols} in CSV. Found: {df_internal.columns.tolist()} <a href='/'>Back</a>")
    except Exception as e:
        return f"Error reading CSV: {e} <a href='/'>Back</a>"

    MERGED_DF = build_merged_df_enhanced(df_internal, SCRAPED_DF, threshold=threshold)
    return render_template_string(results_template, merged_df=MERGED_DF)

@app.route("/download_scraped", methods=["GET"])
def download_scraped():
    global SCRAPED_DF
    if SCRAPED_DF.empty:
        return "No scraped data to download. <a href='/'>Back</a>"
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
