import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse
import logging
import concurrent.futures
import webbrowser
import os

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

# Fungsi untuk pencarian dork dengan subdomain
def google_dork_search_for_keyword(domain, keyword, processed_domains):
    detected_results = []  # Untuk menyimpan hasil domain terindikasi dengan alasan
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
        except requests.exceptions.RequestException as e:
            logger.error(f"Kesalahan saat mengakses Google: {e} (percobaan {attempt}/{retries}).")
        
    if not success:
        logger.error(f"Gagal mendapatkan hasil untuk '{query}' setelah {retries} percobaan.")
        return []

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

    return detected_results

# Fungsi utama untuk menjalankan pencarian paralel
def search_keywords_parallel(domain, keywords):
    all_results = []
    processed_domains = set()  # Set untuk melacak domain yang sudah diproses
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:  # Batasi jumlah thread aktif
        futures = [executor.submit(google_dork_search_for_keyword, domain, keyword, processed_domains) for keyword in keywords]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            all_results.extend(result)
    return all_results

# Fungsi untuk menyimpan log ke folder Downloads
def save_log_to_downloads(log_data):
    # Tentukan path untuk folder Downloads, menyesuaikan dengan OS
    download_folder = os.path.expanduser('~/Downloads')  # Menyesuaikan dengan direktori Downloads
    file_path = os.path.join(download_folder, "log_hasil_pencarian.txt")
    
    # Menulis log ke file di folder Downloads
    with open(file_path, "w") as log_file:
        log_file.write(log_data)
        print(f"Log telah disimpan di: {file_path}")

# Input dari pengguna untuk domain dan URL
user_urls_input = input("Masukkan URL atau domain yang ingin dicari (pisahkan dengan koma): ").strip()
user_urls = [url.strip() for url in user_urls_input.split(",")]

# Daftar kata kunci yang digunakan untuk pencarian
keywords = [
    "slot", "gacor", "scatter", "zeus", "jackpot", "maxwin", "bonus",
    "pragmatic", "taruhan", "judi", "spin", "freebet", "promo",
    "cashback", "deposit", "withdraw", "bandar slot", "slot online",
    "judi terpercaya", "wild", "habanero", "spadegaming", "joker"
]

# Menjalankan pencarian paralel untuk setiap URL yang dimasukkan pengguna
all_results = []
for user_url in user_urls:
    detected_results = search_keywords_parallel(user_url, keywords)
    all_results.extend(detected_results)

# Menampilkan hasil dan memberikan opsi membuka link
log_data = ""
if all_results:
    log_data += "=== Domain/Subdomain Terindikasi Judi Online ===\n"
    for result in all_results:
        log_data += f"- Domain: {result['domain']}\n"
        log_data += f"  Status: Terindikasi Judi Online\n"
        log_data += f"  Alasan: {result['reason']}\n"
        log_data += f"  Snippet: {result['snippet']}\n"
        log_data += f"  Link: {result['link']}\n\n"
        
        print(f"- Domain: {result['domain']}")
        print(f"  Status: Terindikasi Judi Online")
        print(f"  Alasan: {result['reason']}")
        print(f"  Snippet: {result['snippet']}")
        print(f"  Link: {result['link']}\n")
        
        # Opsi untuk membuka link
        open_link = input(f"Apakah Anda ingin membuka link {result['link']}? (y/n): ").strip().lower()
        if open_link == 'y':
            webbrowser.open(result['link'])  # Membuka link di browser
else:
    log_data += "Tidak ada domain/subdomain yang terindikasi judi online.\n"
    print("Tidak ada domain/subdomain yang terindikasi judi online.")

# Menyimpan log ke folder Downloads
save_log_to_downloads(log_data)
