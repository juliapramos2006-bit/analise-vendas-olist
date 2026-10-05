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

# %% 4. Receita e pedidos por mês
mensal = df.groupby("mes").agg(
    receita=("receita", "sum"), pedidos=("order_id", "nunique")
)
ax = mensal["receita"].plot(figsize=(10, 4), marker="o", title="Receita mensal (R$)")
ax.set_xlabel("")
plt.tight_layout()
plt.savefig(IMG / "receita_mensal.png", dpi=150)
plt.show()

# %% 5. Top 10 categorias por receita
top_cat = (
    df.groupby("categoria")["receita"].sum().sort_values(ascending=False).head(10)
)
ax = top_cat.sort_values().plot(
    kind="barh", figsize=(8, 5), title="Top 10 categorias por receita (R$)"
)
ax.set_ylabel("")
plt.tight_layout()
plt.savefig(IMG / "top_categorias.png", dpi=150)
plt.show()

# %% 6. Receita por estado
por_estado = (
    df.groupby("customer_state")["receita"].sum().sort_values(ascending=False).head(10)
)
ax = por_estado.plot(kind="bar", figsize=(8, 4), title="Top 10 estados por receita (R$)")
ax.set_xlabel("")
plt.tight_layout()
plt.savefig(IMG / "receita_por_estado.png", dpi=150)
plt.show()

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

ax = nota.rename({False: "No prazo", True: "Atrasou"}).plot(
    kind="bar", figsize=(5, 4), title="Nota média por entrega"
)
ax.set_xlabel("")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(IMG / "nota_por_atraso.png", dpi=150)
plt.show()

# %% 9. Conclusões (preencha com os SEUS números, depois de rodar)
# - Receita cresceu X% entre jan/2017 e ago/2018
# - As 3 categorias que mais vendem são: ...
# - SP concentra X% da receita
# - Pedidos atrasados têm nota média X vs Y dos entregues no prazo
