import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import logging
import concurrent.futures

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Fungsi untuk pencarian dork dengan subdomain
def google_dork_search_for_keyword(domain, keyword, processed_domains):
    detected_results = []  # Untuk menyimpan hasil domain terindikasi dengan alasan
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    base_url = "https://www.google.com/search"
    query = f"site:*.{domain} {keyword}"
    params = {"q": query, "hl": "id"}

    retries = 3  # Jumlah percobaan
    success = False  # Penanda jika permintaan berhasil

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Mengirim permintaan untuk '{query}' (percobaan {attempt}/{retries})...")
            start_time = time.time()  # Waktu mulai permintaan
            response = requests.get(base_url, headers=headers, params=params, timeout=3)  # Mengurangi timeout
            response.raise_for_status()  # Memunculkan error jika HTTP status bukan 200
            elapsed_time = time.time() - start_time  # Waktu yang dibutuhkan untuk permintaan

            logger.info(f"Permintaan berhasil untuk '{query}' dalam {elapsed_time:.2f} detik.")
            success = True
            break  # Keluar dari loop retry jika berhasil
        except requests.exceptions.Timeout:
            logger.warning(f"Permintaan timeout untuk '{query}' (percobaan {attempt}/{retries}).")
        except requests.exceptions.RequestException as e:
            logger.error(f"Kesalahan saat mengakses Google: {e} (percobaan {attempt}/{retries}).")
        
        time.sleep(1)  # Tunggu 1 detik sebelum mencoba lagi

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

            # Cek apakah domainnya adalah kalselprov.go.id atau subdomainnya dan pastikan domainnya belum diproses
            if (detected_domain.endswith(f".{domain}") or detected_domain == domain) and detected_domain not in processed_domains:
                processed_domains.add(detected_domain)  # Tandai domain sebagai sudah diproses
                detected_results.append({
                    "domain": detected_domain,
                    "reason": f"Keyword '{keyword}' ditemukan.",
                    "snippet": snippet
                })

    return detected_results

# Fungsi utama untuk menjalankan pencarian paralel
def search_keywords_parallel(domain, keywords):
    all_results = []
    processed_domains = set()  # Set untuk melacak domain yang sudah diproses
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(google_dork_search_for_keyword, domain, keyword, processed_domains) for keyword in keywords]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            all_results.extend(result)
    return all_results

# Input dari pengguna untuk domain dan URL
user_urls_input = input("Masukkan URL atau domain yang ingin dicari (pisahkan dengan koma): ").strip()
user_urls = [url.strip() for url in user_urls_input.split(",")]

# Daftar kata kunci yang sudah ada di dalam kode
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

# Menampilkan hasil
if all_results:
    logger.info("=== Domain/Subdomain Terindikasi Judi Online ===")
    for result in all_results:
        print(f"- Domain: {result['domain']}")
        print(f"  Status: Terindikasi Judi Online")
        print(f"  Alasan: {result['reason']}")
        print(f"  Snippet: {result['snippet']}\n")
else:
    logger.info("Tidak ada domain/subdomain yang terindikasi judi online.")