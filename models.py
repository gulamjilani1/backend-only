from peewee import Model, CharField, FloatField, ForeignKeyField, SqliteDatabase
from flask_login import UserMixin

db = SqliteDatabase('invoice.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(UserMixin, BaseModel):
    username = CharField(unique=True)
    password = CharField()

class Customer(BaseModel):
    name = CharField()
    email = CharField()
    phone = CharField()

class Item(BaseModel):
    name = CharField()
    price = FloatField()

class Invoice(BaseModel):
    customer = ForeignKeyField(Customer, backref='invoices')
    total = FloatField()

class InvoiceItem(BaseModel):
    invoice = ForeignKeyField(Invoice, backref='items')
    item = ForeignKeyField(Item)
    quantity = FloatField()

db.connect()
db.create_tables([User, Customer, Item, Invoice, InvoiceItem])
