from peewee import Model, CharField, FloatField, ForeignKeyField, SqliteDatabase

# Database file
db = SqliteDatabase('invoice.db')

class BaseModel(Model):
    class Meta:
        database = db

# Customer table
class Customer(BaseModel):
    name = CharField()
    email = CharField()
    phone = CharField()

# Item table
class Item(BaseModel):
    name = CharField()
    price = FloatField()

# Invoice table
class Invoice(BaseModel):
    customer = ForeignKeyField(Customer, backref='invoices')
    total = FloatField()

# InvoiceItem link (invoice ke andar items)
class InvoiceItem(BaseModel):
    invoice = ForeignKeyField(Invoice, backref='items')
    item = ForeignKeyField(Item)
    quantity = FloatField()

# Tables create karne ke liye
db.connect()
db.create_tables([Customer, Item, Invoice, InvoiceItem])
