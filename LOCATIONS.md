# Zameen.com Location Reference

Quick reference for common Karachi locations and their IDs for the scraper.

## How to Use

Edit `scrape.py` and update these three values:

```python
LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_8'
LOCATION_ID = '10016'
LOCATION_DISPLAY = 'bahria_town_precinct_8'
```

---

## Bahria Town Karachi - Precincts

| Precinct | LOCATION_NAME | LOCATION_ID | LOCATION_DISPLAY |
|----------|---------------|-------------|------------------|
| Precinct 1 | `Bahria_Town_Karachi_Bahria_Town___Precinct_1` | `10009` | `bahria_town_precinct_1` |
| Precinct 2 | `Bahria_Town_Karachi_Bahria_Town___Precinct_2` | `10010` | `bahria_town_precinct_2` |
| Precinct 3 | `Bahria_Town_Karachi_Bahria_Town___Precinct_3` | `10011` | `bahria_town_precinct_3` |
| Precinct 4 | `Bahria_Town_Karachi_Bahria_Town___Precinct_4` | `10012` | `bahria_town_precinct_4` |
| Precinct 5 | `Bahria_Town_Karachi_Bahria_Town___Precinct_5` | `10013` | `bahria_town_precinct_5` |
| Precinct 6 | `Bahria_Town_Karachi_Bahria_Town___Precinct_6` | `10014` | `bahria_town_precinct_6` |
| Precinct 7 | `Bahria_Town_Karachi_Bahria_Town___Precinct_7` | `10015` | `bahria_town_precinct_7` |
| **Precinct 8** | `Bahria_Town_Karachi_Bahria_Town___Precinct_8` | `10016` | `bahria_town_precinct_8` |
| Precinct 9 | `Bahria_Town_Karachi_Bahria_Town___Precinct_9` | `10017` | `bahria_town_precinct_9` |
| Precinct 10 | `Bahria_Town_Karachi_Bahria_Town___Precinct_10` | `10018` | `bahria_town_precinct_10` |
| Precinct 11 | `Bahria_Town_Karachi_Bahria_Town___Precinct_11` | `10019` | `bahria_town_precinct_11` |
| Precinct 12 | `Bahria_Town_Karachi_Bahria_Town___Precinct_12` | `10020` | `bahria_town_precinct_12` |
| Precinct 13 | `Bahria_Town_Karachi_Bahria_Town___Precinct_13` | `10021` | `bahria_town_precinct_13` |
| Precinct 15 | `Bahria_Town_Karachi_Bahria_Town___Precinct_15` | `10023` | `bahria_town_precinct_15` |
| Precinct 16 | `Bahria_Town_Karachi_Bahria_Town___Precinct_16` | `10024` | `bahria_town_precinct_16` |
| Precinct 17 | `Bahria_Town_Karachi_Bahria_Town___Precinct_17` | `10025` | `bahria_town_precinct_17` |
| Precinct 18 | `Bahria_Town_Karachi_Bahria_Town___Precinct_18` | `10026` | `bahria_town_precinct_18` |
| Precinct 19 | `Bahria_Town_Karachi_Bahria_Town___Precinct_19` | `10027` | `bahria_town_precinct_19` |
| Precinct 25 | `Bahria_Town_Karachi_Bahria_Town___Precinct_25` | `10031` | `bahria_town_precinct_25` |
| Precinct 27 | `Bahria_Town_Karachi_Bahria_Town___Precinct_27` | `10033` | `bahria_town_precinct_27` |

## Bahria Town Karachi - General

| Location | LOCATION_NAME | LOCATION_ID | LOCATION_DISPLAY |
|----------|---------------|-------------|------------------|
| All Bahria Town | `Bahria_Town_Karachi` | `8298` | `bahria_town_karachi` |
| Midway Commercial | `Bahria_Town_Karachi_Midway_Commercial` | `11304` | `bahria_town_midway_commercial` |

## DHA Karachi

| Location | LOCATION_NAME | LOCATION_ID | LOCATION_DISPLAY |
|----------|---------------|-------------|------------------|
| DHA Phase 5 | `DHA_Phase_5_Karachi` | `2` | `dha_phase_5` |
| DHA Phase 6 | `DHA_Phase_6_Karachi` | `3` | `dha_phase_6` |
| DHA Phase 7 | `DHA_Phase_7_Karachi` | `4` | `dha_phase_7` |
| DHA Phase 8 | `DHA_Phase_8_Karachi` | `5` | `dha_phase_8` |

## Other Popular Areas

| Location | LOCATION_NAME | LOCATION_ID | LOCATION_DISPLAY |
|----------|---------------|-------------|------------------|
| Clifton | `Clifton_Karachi` | `6` | `clifton` |
| Gulshan-e-Iqbal | `Gulshan-e-Iqbal_Karachi` | `10` | `gulshan_e_iqbal` |
| Malir | `Malir_Karachi` | `16` | `malir` |

---

## How to Find Location ID

If your desired location is not listed above:

1. Go to zameen.com
2. Search for properties in your desired location
3. Look at the URL, it will be like:
   ```
   https://www.zameen.com/Homes/Karachi_YOUR_LOCATION-12345-1.html
   ```
4. The number before `-1.html` is your LOCATION_ID (e.g., `12345`)
5. The part after `Karachi_` and before the ID is your LOCATION_NAME (e.g., `YOUR_LOCATION`)

---

## Example Configuration

### For Precinct 6:
```python
LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_6'
LOCATION_ID = '10014'
LOCATION_DISPLAY = 'bahria_town_precinct_6'
```

### For DHA Phase 5:
```python
LOCATION_NAME = 'DHA_Phase_5_Karachi'
LOCATION_ID = '2'
LOCATION_DISPLAY = 'dha_phase_5'
```

---

## Anti-Scraping Measures Built-in

The scraper includes:
- ✅ Random delays between pages (3-6 seconds)
- ✅ User agent rotation
- ✅ Headless browser (Playwright) to handle JavaScript
- ✅ Network idle waiting (waits for page to fully load)
- ✅ Polite scraping pace (not hammering the server)

**Recommendation:** Don't scrape more than 10 pages at once to stay polite and avoid detection.
