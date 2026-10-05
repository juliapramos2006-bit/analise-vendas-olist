# %% [markdown]
# # Análise de vendas de e-commerce — Olist (Brasil)
# Dataset: "Brazilian E-Commerce Public Dataset by Olist" (Kaggle)
# Perguntas de negócio:
# 1. Como as vendas evoluíram ao longo do tempo?
# 2. Quais categorias geram mais receita?
# 3. Quais estados mais compram?
# 4. Qual o ticket médio?
# 5. Entrega no prazo influencia a nota de avaliação?

# %% Imports
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # salva os gráficos em arquivo, sem abrir janelas
import matplotlib.pyplot as plt
import pandas as pd

DATA = Path("data")        # coloque os CSVs do Kaggle nesta pasta
IMG = Path("images")       # os gráficos serão salvos aqui
IMG.mkdir(exist_ok=True)

# %% 1. Carregar os dados
orders = pd.read_csv(
    DATA / "olist_orders_dataset.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
)
items = pd.read_csv(DATA / "olist_order_items_dataset.csv")
products = pd.read_csv(DATA / "olist_products_dataset.csv")
customers = pd.read_csv(DATA / "olist_customers_dataset.csv")
reviews = pd.read_csv(DATA / "olist_order_reviews_dataset.csv")
translation = pd.read_csv(DATA / "product_category_name_translation.csv")

# %% 2. Conhecer e limpar
print(orders.shape, items.shape, products.shape)
print(orders["order_status"].value_counts())
print(orders.isna().sum())

# Só pedidos entregues entram na análise de receita
orders = orders[orders["order_status"] == "delivered"].copy()

# O dataset tem poucos pedidos em 2016 e no fim de 2018: foca no período completo
orders = orders[
    (orders["order_purchase_timestamp"] >= "2017-01-01")
    & (orders["order_purchase_timestamp"] < "2018-09-01")
]

# %% 3. Juntar as tabelas
df = (
    orders.merge(items, on="order_id")
    .merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    .merge(translation, on="product_category_name", how="left")
    .merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
)
df["receita"] = df["price"]  # sem frete
df["mes"] = df["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
df["categoria"] = df["product_category_name_english"].fillna("outros")
receita_total = df["receita"].sum()

# %% 4. Receita e pedidos por mês
mensal = df.groupby("mes").agg(
    receita=("receita", "sum"), pedidos=("order_id", "nunique")
)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(mensal.index, mensal["receita"], marker="o")
ax.set_title("Receita mensal (R$)")
fig.tight_layout()
fig.savefig(IMG / "receita_mensal.png", dpi=150)
plt.close(fig)

# %% 5. Top 10 categorias por receita
top_cat = df.groupby("categoria")["receita"].sum().sort_values(ascending=False).head(10)

fig, ax = plt.subplots(figsize=(8, 5))
top_cat.sort_values().plot(kind="barh", ax=ax)
ax.set_title("Top 10 categorias por receita (R$)")
ax.set_ylabel("")
fig.tight_layout()
fig.savefig(IMG / "top_categorias.png", dpi=150)
plt.close(fig)

# %% 6. Receita por estado
por_estado = (
    df.groupby("customer_state")["receita"].sum().sort_values(ascending=False).head(10)
)

fig, ax = plt.subplots(figsize=(8, 4))
por_estado.plot(kind="bar", ax=ax)
ax.set_title("Top 10 estados por receita (R$)")
ax.set_xlabel("")
fig.tight_layout()
fig.savefig(IMG / "receita_por_estado.png", dpi=150)
plt.close(fig)

# %% 7. Ticket médio (receita por pedido)
ticket_medio = df.groupby("order_id")["receita"].sum().mean()
print(f"Ticket médio: R$ {ticket_medio:,.2f}")

# %% 8. Entrega no prazo x nota de avaliação
entregas = orders.merge(reviews[["order_id", "review_score"]], on="order_id")
entregas["atrasou"] = (
    entregas["order_delivered_customer_date"] > entregas["order_estimated_delivery_date"]
)
nota = entregas.groupby("atrasou")["review_score"].mean()
print(nota)
print(f"% de pedidos atrasados: {entregas['atrasou'].mean():.1%}")

fig, ax = plt.subplots(figsize=(5, 4))
nota.rename({False: "No prazo", True: "Atrasou"}).plot(kind="bar", ax=ax)
ax.set_title("Nota média por entrega")
ax.set_xlabel("")
ax.tick_params(axis="x", rotation=0)
fig.tight_layout()
fig.savefig(IMG / "nota_por_atraso.png", dpi=150)
plt.close(fig)

# %% 9. Números extras para o README
pct_sp = por_estado.iloc[0] / receita_total
print(f"Estado líder: {por_estado.index[0]} com {pct_sp:.1%} da receita")

print("Participação das 3 maiores categorias:")
print((top_cat.head(3) / receita_total).round(3))
print(f"As 3 juntas: {top_cat.head(3).sum() / receita_total:.1%}")

# Crescimento ano contra ano, comparando os mesmos meses (jan-ago)
r2017 = mensal.loc["2017-01":"2017-08", "receita"].sum()
r2018 = mensal.loc["2018-01":"2018-08", "receita"].sum()
print(f"Jan-Ago 2017: R$ {r2017:,.0f}")
print(f"Jan-Ago 2018: R$ {r2018:,.0f}")
print(f"Crescimento: {r2018 / r2017 - 1:.0%}")

print("Gráficos salvos na pasta images/")
