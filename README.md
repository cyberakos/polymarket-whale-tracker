# 🐋 Polymarket Whale Consensus & Alpha Radar

Valós idejű, intézményi méretű megbízásokat és bálna-tőkeáramlásokat figyelő döntéstámogató rendszer a **Polymarket** predikciós piacaihoz. Az alkalmazás automatikusan azonosítja a legeredményesebb kereskedőket, klaszterezést végez az aktív pozícióikon, kimutatja a csoportos konszenzust (smart money overlap), és a **Fél-Kelly-kritérium** alapján optimális tétméret-javaslatot ad.

---

## 📌 Főbb Jellemzők

* **Élő Leaderboard Integráció (Data API):** A Polymarket legeredményesebb kereskedőinek automatikus lekérése valós PnL és volumen alapján a `/v1/leaderboard` végpontról.
* **Párhuzamosított Adatgyűjtés (`ThreadPoolExecutor`):** Akár 50–200 bálna élő, nyitott fogadásainak másodpercek alatti párhuzamos lekérése.
* **Dinamikus Kimenetel- és Piackezelés:** Helyesen kezeli a bináris (`YES` / `NO`), valamint a két- és többesélyes sportpiacokat (pl. valódi csapatnevek, hendikepek/spreads).
* **Kvantitatív Konszenzus Motor:**
  * Konszenzus arány (%) és domináns tőke számítása.
  * Súlyozott átlagos belépési ár (**VWAP**).
  * A résztvevő bálnák átlagos történelmi találati aránya (Win Rate).
* **Pozícióméretezés & Kockázatkezelés:**
  * **Opportunity Score (0–100%):** A konszenzus erejét, bálnák számát, tőkét és piaci félreárazást összegző kvantitatív pontszám.
  * **Bináris Fél-Kelly-méretezés:** Matematikailag optimalizált tétnagyság a megadott portfólióméret alapján, 10%-os kockázati sapkával (`Safety Cap`).
* **Interaktív Streamlit Felület:**
  * Valós idejű KPI kártyák és rendezhető, szűrhető konszenzus táblázat.
  * **Közvetlen piaclinkek (`LinkColumn`):** Egy kattintással megnyitható az élő esemény a Polymarketen.
  * **Deep-Dive Tárcavizsgáló:** Részletes lista arról, hogy az adott piacon melyik bálna mekkora összeggel és milyen áron van bent.
* **Hálózati Hibatűrés:** Beépített proxy-támogatás és determinisztikus szintetikus mock-generátor API-kimaradás esetére.

---

## 🏗️ Projektstruktúra

```text
polymarket_whale_tracker/
├── config.py              # Konfiguráció, API URL-ek, küszöbértékek
├── models.py              # Pydantic modellek (Trader, Position, ConsensusMarket)
├── client.py              # Polymarket Data & Gamma API kliens (többszálú)
├── analytics.py           # Konszenzus-algoritmus, Opportunity Score és Kelly-méretezés
├── app.py                 # Streamlit webes dashboard és vizualizáció
├── test_connection.py     # Hálózati és API kapcsolat-ellenőrző segédszkript
├── requirements.txt       # Szükséges Python könyvtárak
└── README.md              # Rendszerleírás és dokumentáció
📐 Matematikai és Döntési Logika1. Opportunity Score (0 – 100 pont)Az algoritmus az alábbi faktorokat súlyozza:Konszenzus Arány (max. 35 pont): A domináns kimenetel tőkeértéke a teljes bálna-kitettséghez viszonyítva.Bálnák Száma (max. 25 pont): Hány különálló top kereskedő van ugyanazon a kimenetelen (8+ bálnánál éri el a maximumot).Kereskedői Minőség (max. 20 pont): A domináns oldalon álló bálnák átlagos nyerési aránya (Win Rate).Tőke Koncentráció (max. 15 pont): Logaritmikusan skálázott dollár-kitettség.Árelőny (max. 5 pont): Mennyire van még diszkont az aktuális piaci áron (1 - ár).2. Bináris Opciós Kelly-méretezésA modell predikciós piacokra optimalizált Kelly-képletet használ:$$f^* = \lambda \cdot \frac{p - c}{1 - c}$$$c \in (0, 1)$: a piac aktuális belépési ára (implikált piaci esély),$p$: a bálnák konszenzusa és átlagos találati aránya alapján korrigált becsült valószínűség,$\lambda$: kockázati szorzó (alapértelmezett: $0.5$ a Fél-Kelly stratégiához a variancia csökkentése érdekében),A javasolt tétösszeg maximum a teljes tőke 10%-a lehet az egyedi pozíciókockázat elkerülésére.🚀 Telepítés és Beüzemelés1. ElőfeltételekPython 3.10 vagy újabb.Hálózati kapcsolat: Magyarországi internetszolgáltatók esetén az SNI/DPI blokkolás miatt az API eléréséhez ajánlott az ingyenes Cloudflare 1.1.1.1 with WARP (vagy tetszőleges VPN / Proxy) használata.2. Függőségek telepítéseBash# Klónozd a tárolót
git clone [https://github.com/](https://github.com/)<felhasznalonev>/polymarket-whale-tracker.git
cd polymarket-whale-tracker

# Virtuális környezet létrehozása és aktiválása (opcionális, de javasolt)
python -m venv venv

# Windows aktiválás:
venv\Scripts\activate
# Linux/macOS aktiválás:
source venv/bin/activate

# Csomagok telepítése
python -m pip install -r requirements.txt
3. API kapcsolat ellenőrzéseMielőtt elindítod a webes felületet, teszteld a kapcsolatot:Bashpython test_connection.py
Ha a válaszban megjelenik egy aktív piac címe és a ranglista #1 kereskedője (pl. Theo4), a rendszer közvetlenül eléri az élő adatokat.4. A Dashboard indításaBashpython -m streamlit run app.py
A kezelőfelület automatikusan megnyílik a böngészőben: http://localhost:8501.⚙️ Dashboard Paraméterek (Sidebar)Vizsgált Top Bálnák Száma: 25 és 200 között állítható, hány élvonalbeli kereskedő tárcáját olvassa be és elemezze a motor.Kereskedési Tőke (USD): A bankroll összege, amelyből a Kelly-motor kiszámolja az ajánlott tétméretet.Kelly Kockázati Profil: 0.25x és 1.0x között skálázható tőkearány (0.5x az ajánlott Fél-Kelly).Minimális Bálna Egyezés: Küszöbérték arra, hogy legalább hány bálnának kell azonos oldalon állnia (alapértelmezett: 3).Minimális Konszenzus Arány (%): Minimális dominancia-arány az adott oldalon (pl. 75%+).Automatikus Frissítés: Állítható intervallum (30 mp, 60 mp, 120 mp stb.) a friss piaci adatok betöltéséhez.⚠️ Figyelmeztetés (Disclaimer)Ez a szoftver kizárólag kutatási, kísérleti és döntéstámogatási célokat szolgál. Nem minősül pénzügyi, befektetési vagy adótanácsadásnak. A predikciós piacokon végzett kereskedés jelentős kockázattal jár. Minden esetben végezz saját kockázatkezelési és piacellenőrzési felmérést a tőkéd allokálása előtt!