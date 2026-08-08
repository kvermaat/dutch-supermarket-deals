# 🛒 Dutch Supermarket Deals

A Home Assistant custom integration and Lovelace card for finding supermarket deals in the Netherlands using data from [PrijsProfeet](https://www.prijsprofeet.nl).

Dutch Supermarket Deals lets you create a shared watchlist of supermarket products and automatically shows matching current offers from selected Dutch supermarkets.

## ✨ Features

- Search current Dutch supermarket deals
- Shared watched-product list stored in Home Assistant
- Select which supermarkets to include
- Set a minimum discount per watched product
- Filter products by PrijsProfeet category
- Exclude unwanted words or phrases
- Sort offers by:
  - Highest discount
  - Lowest price
  - Biggest saving in euros
  - Store
- Optional "Best deal only" mode
- List or multi-column grid layout
- Configurable number of columns
- Product images
- Current price, original price and discount
- Edit and remove watched products directly from the card
- Responsive layout for desktop, tablet and mobile

## 🏪 Supported supermarkets

The integration can work with supermarkets available through PrijsProfeet, including:

- Albert Heijn
- Jumbo
- PLUS
- Dirk
- Aldi
- Lidl
- Ekoplaza
- Hoogvliet
- DekaMarkt
- Vomar

Availability depends on the data provided by PrijsProfeet.

## 📦 Installation with HACS

### Custom repository

Until Dutch Supermarket Deals is included in the default HACS repository list, add it as a custom repository.

1. Open HACS in Home Assistant.
2. Open the menu in the top-right corner.
3. Select **Custom repositories**.
4. Add:https://github.com/kvermaat/dutch-supermarket-deals

5. Select **Integration** as the repository type.
6. Install **Dutch Supermarket Deals**.
7. Restart Home Assistant.

After restarting:

1. Go to **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Dutch Supermarket Deals**.
4. Complete the setup.

## 🛒 Watched products

Products are added directly from the Dutch Supermarket Deals dashboard card.

Example:

```text
Product:
Calve pindakaas

Category:
ontbijt

Exclude words:
(empty)

Minimum discount:
10% 
