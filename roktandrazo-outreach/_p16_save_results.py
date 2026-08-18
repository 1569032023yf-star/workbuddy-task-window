#!/usr/bin/env python3
# P1.6 批次 B/C 结果落盘
import json

batchB = [
    {"name": "Gear Gaming", "city": "Fayetteville", "state": "AR",
     "website": "https://www.geargamingstore.com", "website_valid": True,
     "website_note": "官方站点", "official_email": "fayetteville@geargamingstore.com",
     "evidence_url": "http://fayetteville.geargamingstore.com/pages/contact-us",
     "evidence_snippet": "Contact Us: Address 3029 North College Ave, Fayetteville; Phone (479)276-8110; Email fayetteville@geargamingstore.com",
     "status": "EMAIL_FOUND"},
    {"name": "IMAGINE! Hobbies & Games", "city": "Sherwood", "state": "AR",
     "website": "https://imaginegamez.wordpress.com", "website_valid": True,
     "website_note": "官方博客", "official_email": "", "status": "NO_EMAIL"},
    {"name": "Shannon's Cards & Comics", "city": "Wynne", "state": "AR",
     "website": "", "website_valid": False, "website_note": "wixsite 404",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "The Bat Cave", "city": "Conway", "state": "AR",
     "website": "", "website_valid": False, "website_note": "门店已关",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "The Gamer Utopia", "city": "Rogers", "state": "AR",
     "website": "", "website_valid": False, "website_note": "域名出售",
     "official_email": "", "status": "WEBSITE_INVALID"},
    {"name": "2D10 Games", "city": "Ft. Myers", "state": "FL",
     "website": "", "website_valid": False, "website_note": "已关闭",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Anthem Games", "city": "Tampa", "state": "FL",
     "website": "", "website_valid": False, "website_note": "官网不可达",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Armada Games", "city": "Temple Terrace", "state": "FL",
     "website": "https://shoparmada.com", "website_valid": True,
     "website_note": "官方商店", "official_email": "info@armadagames.com",
     "evidence_url": "https://shoparmada.com/pages/contact-us",
     "evidence_snippet": "Contact Us: General Questions info@armadagames.com; Order armadaorders@armadagames.com",
     "status": "EMAIL_FOUND"},
    {"name": "Bobe's Hobby House", "city": "Pensacola", "state": "FL",
     "website": "", "website_valid": False, "website_note": "域名被劫持",
     "official_email": "", "status": "WEBSITE_INVALID"},
    {"name": "Book & Game Emporium", "city": "Fort Walton Beach", "state": "FL",
     "website": "https://www.bookandgames.net", "website_valid": True,
     "website_note": "官方商店", "official_email": "", "status": "NO_EMAIL"},
]

batchC = [
    {"name": "Borderlands Comics & Games", "city": "Jacksonville", "state": "FL",
     "website": "", "website_valid": False, "website_note": "已被收购更名",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Broadsword", "city": "Orange Park", "state": "FL",
     "website": "", "website_valid": False, "website_note": "无官网",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Comic Emporium", "city": "Panama City", "state": "FL",
     "website": "http://comicemporium.net/", "website_valid": True,
     "website_note": "官方站点", "official_email": "", "status": "NO_EMAIL"},
    {"name": "Comics & Games Tallahassee", "city": "Tallahassee", "state": "FL",
     "website": "", "website_valid": False, "website_note": "无官网",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Cool Comics & Games", "city": "Cape Coral", "state": "FL",
     "website": "http://www.coolcomicsandgames.com/", "website_valid": True,
     "website_note": "官方单页站", "official_email": "", "status": "NO_EMAIL"},
    {"name": "Cool Stuff Games", "city": "Winter Park", "state": "FL",
     "website": "https://www.coolstuffgames.com/", "website_valid": True,
     "website_note": "连锁官方站", "official_email": "Info@CoolStuffInc.com",
     "evidence_url": "https://www.coolstuffinc.com/main_contact.php",
     "evidence_snippet": "Contact Information: Email: Info@CoolStuffInc.com",
     "status": "EMAIL_FOUND"},
    {"name": "DCD Games", "city": "St. Augustine", "state": "FL",
     "website": "", "website_valid": False, "website_note": "无官网",
     "official_email": "", "status": "NO_WEBSITE"},
    {"name": "Dogs of War Gaming", "city": "Palm Bay", "state": "FL",
     "website": "https://dogsofwargaming.square.site/", "website_valid": True,
     "website_note": "Square店铺", "official_email": "", "status": "NO_EMAIL"},
    {"name": "Emerald City", "city": "Clearwater", "state": "FL",
     "website": "https://emeraldcitycomics.com/", "website_valid": True,
     "website_note": "官方站点", "official_email": "email@emeraldcitycomics.com",
     "evidence_url": "https://emeraldcitycomics.com/",
     "evidence_snippet": "Visit us 4902 113th Ave N Clearwater, FL 33760 727-398-2665 email@emeraldcitycomics.com",
     "status": "EMAIL_FOUND"},
    {"name": "Fallout Comics", "city": "Tallahassee", "state": "FL",
     "website": "http://falloutcomics.com/", "website_valid": True,
     "website_note": "官方站点", "official_email": "info@falloutcomics.com",
     "evidence_url": "http://www.falloutcomics.com/privacy-policy/",
     "evidence_snippet": "Company: Fallout Comics Email: info@falloutcomics.com Postal: 1482 Apalachee Pkwy, Tallahassee FL 32301",
     "status": "EMAIL_FOUND"},
]

json.dump(batchB, open("output/p16_laneA_batch2.json", "w"), ensure_ascii=False, indent=2)
json.dump(batchC, open("output/p16_laneA_batch3.json", "w"), ensure_ascii=False, indent=2)
batchA = json.load(open("output/p16_laneA_batch1.json"))
all30 = batchA + batchB + batchC
json.dump(all30, open("output/p16_verified_results.json", "w"), ensure_ascii=False, indent=2)

found = [r for r in all30 if r["status"] == "EMAIL_FOUND"]
print("total:", len(all30), "| EMAIL_FOUND:", len(found))
for r in found:
    print(f"  {r['name']:<28} {r['official_email']}")
print()
# 漏斗统计
from collections import Counter
st = Counter(r["status"] for r in all30)
print("status分布:", dict(st))
