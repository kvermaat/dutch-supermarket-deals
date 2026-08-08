# 🛒 Dutch Supermarket Deals

A Home Assistant custom integration and Lovelace card for finding supermarket deals in the Netherlands using data from PrijsProfeet.

Dutch Supermarket Deals lets you create a shared watchlist of supermarket products and automatically shows matching current offers from selected Dutch supermarkets.

## 👋 About this project

I'm not a software developer. This project started as a personal idea for my own Home Assistant setup and grew into something I thought could be useful to other people as well.

ChatGPT helped me turn the idea into a working Home Assistant integration, understand the code, troubleshoot problems, and prepare the project for sharing with the community.

I'm continuing to learn as I work on the project, so feedback, bug reports and contributions are very welcome.

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

Until Dutch Supermarket Deals is available directly through HACS, add it as a custom repository.

1. Open HACS in Home Assistant.
2. Open the menu in the top-right corner.
3. Select **Custom repositories**.
4. Add:

```text
https://github.com/kvermaat/dutch-supermarket-deals
```

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
```

The integration searches PrijsProfeet and only displays offers matching the configured filters.

## 🔍 Product filtering

### Product

The product field is the search query sent to PrijsProfeet.

Examples:

```text
Calve pindakaas
Hertog Jan
Coca Cola
courgette
```

### Category

Category is optional.

When supplied, the product must have the same `unified_category` returned by PrijsProfeet.

Example:

```text
groente-fruit
```

A useful setup for courgette could be:

```text
Product:
courgette

Category:
groente-fruit

Exclude words:
mix, honig, bakplaat
```

### Exclude words

Multiple excluded words or phrases can be entered separated by commas.

Example:

```text
mix, honig, bakplaat
```

If any excluded word or phrase occurs in the product name, that result is hidden.

## 💰 Sorting

Offers can be sorted by:

- **Highest discount**
- **Lowest price**
- **Biggest saving €**
- **Store**

## ⭐ Best deal only

When **Best deal only** is enabled, only one matching offer is displayed for each watched product.

The selected sorting method determines which offer is considered the best.

For example:

```text
Sort offers by:
Lowest price

Best deal only:
Enabled
```

This shows the cheapest matching offer for each watched product.

If the cheapest supermarket is disabled in the card settings, the next cheapest matching supermarket is shown instead.

## 🏪 Supermarket filtering

Supermarkets can be enabled or disabled from the card configuration.

For example, if Dirk is disabled, Dirk offers are excluded from the results.

## 🖥️ Card layout

The card supports two layouts.

### List

A single-column compact layout.

### Grid

A configurable multi-column grid.

Available column counts:

```text
1
2
3
4
```

The layout automatically adapts to smaller screens.

## 🔄 Shared lists

Each card has a **Shared list ID**.

Cards using the same list ID share the same watched products through Home Assistant.

Example:

```text
default
```

This allows the same watchlist to be used on multiple dashboards and devices.

## 🌐 Data source

Supermarket product and pricing data is supplied by PrijsProfeet.

https://www.prijsprofeet.nl

Dutch Supermarket Deals is an independent Home Assistant community project and is not affiliated with PrijsProfeet or any supermarket listed by the integration.

Product availability, prices, promotions and supermarket coverage depend on the information supplied by PrijsProfeet.

## 🐛 Issues

Found a bug or have a feature request?

Please create an issue:

https://github.com/kvermaat/dutch-supermarket-deals/issues

When reporting a problem, please include:

- Home Assistant version
- Dutch Supermarket Deals version
- Browser/device if the problem affects the card
- Relevant Home Assistant logs
- Product search and filters used when applicable

## 🤝 Contributing

Contributions, bug reports and improvements are welcome.

I'm learning as I go, so help from experienced Home Assistant and Python developers is especially appreciated.

Repository:

https://github.com/kvermaat/dutch-supermarket-deals

## 📄 License

Dutch Supermarket Deals is released under the MIT License.

See `LICENSE` for details.

The license applies to the source code of Dutch Supermarket Deals. Third-party services, product data, trademarks and logos remain the property of their respective owners.
