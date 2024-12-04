import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse
import logging
import concurrent.futures
import os
import tldextract

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Daftar User-Agent untuk rotasi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

# Fungsi untuk memilih User-Agent acak
def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Fungsi untuk mendapatkan domain dan subdomain dari URL
def extract_domain_and_subdomain(url):
    ext = tldextract.extract(url)
    domain = ext.domain + '.' + ext.suffix  # Domain utama
    subdomain = ext.subdomain  # Subdomain (jika ada)
    return domain, subdomain

# Fungsi untuk pencarian dork dengan subdomain
def google_dork_search_for_keyword(domain, keyword, processed_domains):
    detected_results = []  # Untuk menyimpan hasil domain terindikasi dengan alasan
    failed_results = []  # Untuk menyimpan domain yang gagal diakses dan alasannya
    headers = {
        "User-Agent": get_random_user_agent()
    }
    base_url = "https://www.google.com/search"
    query = f"site:*.{domain} {keyword}"
    params = {"q": query, "hl": "id"}

    retries = 3  # Jumlah percobaan
    success = False  # Penanda jika permintaan berhasil

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Mengirim permintaan untuk '{query}' (percobaan {attempt}/{retries})...")
            time.sleep(random.uniform(2, 6))  # Delay acak antara 2 hingga 6 detik
            response = requests.get(base_url, headers=headers, params=params, timeout=5)
            response.raise_for_status()  # Memunculkan error jika HTTP status bukan 200
            success = True
            break  # Keluar dari loop retry jika berhasil
        except requests.exceptions.Timeout:
            logger.warning(f"Permintaan timeout untuk '{query}' (percobaan {attempt}/{retries}).")
            failed_results.append({
                "domain": domain,
                "reason": "Timeout saat mengakses Google"
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Kesalahan saat mengakses Google: {e} (percobaan {attempt}/{retries}).")
            failed_results.append({
                "domain": domain,
                "reason": f"Kesalahan HTTP: {e}"
            })
        
    if not success:
        logger.error(f"Gagal mendapatkan hasil untuk '{query}' setelah {retries} percobaan.")
        return [], failed_results  # Mengembalikan hasil gagal jika tidak berhasil

    # Proses hasil jika permintaan berhasil
    soup = BeautifulSoup(response.text, "html.parser")
    for g in soup.find_all('div', class_='tF2Cxc'):
        link = g.find('a')['href'] if g.find('a') else None
        snippet = g.find('span', class_='aCOpRe').text if g.find('span', class_='aCOpRe') else ""
        if link:
            # Ekstrak domain dari link
            parsed_url = urlparse(link)
            detected_domain = parsed_url.netloc

            # Cek apakah domainnya adalah target utama atau subdomainnya
            if (detected_domain.endswith(f".{domain}") or detected_domain == domain) and detected_domain not in processed_domains:
                processed_domains.add(detected_domain)  # Tandai domain sebagai sudah diproses
                detected_results.append({
                    "domain": detected_domain,
                    "link": link,
                    "reason": f"Keyword '{keyword}' ditemukan.",
                    "snippet": snippet
                })

    return detected_results, failed_results

# Fungsi utama untuk menjalankan pencarian paralel
def search_keywords_parallel(domain, keywords):
    all_results = []
    failed_results = []
    processed_domains = set()  # Set untuk melacak domain yang sudah diproses
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:  # Batasi jumlah thread aktif
        futures = [executor.submit(google_dork_search_for_keyword, domain, keyword, processed_domains) for keyword in keywords]
        for future in concurrent.futures.as_completed(futures):
            result, failed = future.result()
            all_results.extend(result)
            failed_results.extend(failed)
    return all_results, failed_results

# Fungsi untuk menyimpan hasil pencarian ke file HTML dengan CSS
def save_results_to_html(results, failed_results):
    # Tentukan path untuk folder Downloads, menyesuaikan dengan OS
    download_folder = os.path.expanduser('~/Downloads')  # Menyesuaikan dengan direktori Downloads
    file_path = os.path.join(download_folder, "hasil_pencarian.html")

    # HTML template dengan CSS dan JavaScript
    html_content = """
    <html>
    <head>
        <title>Hasil Pencarian Dorking Google</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                color: #333;
                padding: 40px;
                display: flex;
                justify-content: center;
            }
            .container {
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 1200px;
                padding: 20px;
                overflow: hidden;
            }
            h1 {
                text-align: center;
                font-size: 2rem;
                margin-bottom: 20px;
                color: #4CAF50;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            td {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
                transition: background-color 0.3s ease;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
                transition: color 0.3s ease;
            }
            a:hover {
                color: #007BFF;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hasil Pencarian Dorking Google</h1>
            <table>
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th>Status</th>
                        <th>Alasan</th>
                        <th>Snippet</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
    """

    if results:
        for result in results:
            html_content += f"""
            <tr>
                <td>{result['domain']}</td>
                <td>Terindikasi Judi Online</td>
                <td>{result['reason']}</td>
                <td>{result['snippet']}</td>
                <td><a href="{result['link']}" target="_blank">Link</a></td>
            </tr>
            """
    else:
        html_content += "<tr><td colspan='5'>Tidak ada hasil ditemukan.</td></tr>"

    html_content += "</tbody></table>"

    # Menambahkan informasi domain yang berhasil dan gagal diakses
    html_content += f"""
        <div>
            <h2>Informasi Hasil Pencarian</h2>
            <p><strong>{len(results)}</strong> domain berhasil ditemukan.</p>
            <p><strong>{len(failed_results)}</strong> domain gagal diakses.</p>
            <h3>Alasan Kegagalan:</h3>
            <ul>
    """
    
    for failed in failed_results:
        html_content += f"<li>{failed['domain']}: {failed['reason']}</li>"

    html_content += "</ul></div></div></body></html>"

    # Menyimpan ke file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"File HTML berhasil disimpan di {file_path}")

# Contoh penggunaan
if _name_ == "_main_":
    url_input = input("Masukkan URL (contoh: https://example.com): ")
    domain, subdomain = extract_domain_and_subdomain(url_input)
    print(f"Domain utama: {domain}")
    if subdomain:
        print(f"Subdomain: {subdomain}")
    
    # Menambahkan lebih banyak keyword yang berkaitan dengan judi online
    keywords = [
        "slot", "gacor", "scatter", "zeus", "jackpot", "maxwin", "bonus",
    "pragmatic", "taruhan", "judi", "spin", "freebet", "promo",
    "cashback", "deposit", "withdraw", "bandar slot", "slot online",
    "judi terpercaya", "wild", "habanero", "spadegaming", "joker", "toto", "thailand",
    "game slot", "slot gacor", "slot jackpot", "casino online", "taruhan bola",
    "betting", "poker online", "roulette", "slot machine", "live casino",
    "judi bola", "sportsbook", "mega jackpot", "lottery", "online casino",
    "poker taruhan", "online slots", "play for money", "virtual betting", "high roller", "slot terbaik",
    ]
    
    results, failed_results = search_keywords_parallel(domain, keywords)
    save_results_to_html(results, failed_results)