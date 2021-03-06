from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import desc, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import and_, func, select, or_

from src import db, BaseMixin, ReprMixin
from src.orders.models import Item
from src.user.models import RetailShop


class Brand(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(55), nullable=False, index=True)
    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True)

    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False, backref='brands')
    products = db.relationship('Product', uselist=True, back_populates='brand')
    distributors = db.relationship('Distributor', back_populates='brands', secondary='brand_distributor',
                                   lazy='dynamic')


class ProductTax(BaseMixin, db.Model, ReprMixin):

    tax_id = db.Column(UUID, db.ForeignKey('tax.id'), index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True)

    tax = db.relationship('Tax', foreign_keys=[tax_id])
    product = db.relationship('Product', foreign_keys=[product_id])

    UniqueConstraint(tax_id, product_id)

    @hybrid_property
    def retail_shop_id(self):
        return self.product.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Product.retail_shop_id]).where(Product.id == self.product_id).as_scalar()


class Tax(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(25), nullable=False, index=True)
    value = db.Column(db.Float(precision=2), nullable=False)
    is_disabled = db.Column(db.Boolean(), default=False)

    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True, nullable=False)

    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False, backref='taxes')
    products = db.relationship('Product', back_populates='taxes', secondary='product_tax', lazy='dynamic')

    UniqueConstraint(name, retail_shop_id)


class Distributor(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(127), nullable=False, index=True)
    phone_numbers = db.Column(db.JSON)
    emails = db.Column(db.JSON)

    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True, nullable=False)

    bills = db.relationship('DistributorBill', uselist=True, back_populates='distributor', lazy='dynamic')

    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False, backref='distributors')
    brands = db.relationship('Brand', back_populates='distributors', secondary='brand_distributor')

    UniqueConstraint(name, retail_shop_id)

    @hybrid_property
    def retail_shop_name(self):
        return self.retail_shop.name

    @retail_shop_name.expression
    def retail_shop_name(self):
        return select([RetailShop.name]).where(RetailShop.id == self.retail_shop_id).as_scalar()

    @hybrid_property
    def products(self):
        return Product.query.filter(Product.is_disabled == False, Product.brand_id.in_
                                    ([i[0] for i in BrandDistributor.query.with_entities(BrandDistributor.brand_id)
                                     .filter(BrandDistributor.distributor_id == self.id).all()])).all()


class DistributorBill(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['id', 'distributor_id']

    purchase_date = db.Column(db.Date, nullable=False)
    reference_number = db.Column(db.String(55), nullable=True)
    distributor_id = db.Column(UUID, db.ForeignKey('distributor.id'), nullable=False, index=True)

    distributor = db.relationship('Distributor', single_parent=True, back_populates='bills')
    purchased_items = db.relationship('Stock', uselist=True, back_populates='distributor_bill', lazy='dynamic')

    @hybrid_property
    def bill_amount(self):
        return self.purchased_items.with_entities(func.Sum(Stock.purchase_amount)).scalar()

    @hybrid_property
    def total_items(self):
        return self.purchased_items.with_entities(func.Count(Stock.id)).scalar()

    @hybrid_property
    def retail_shop_id(self):
        return self.distributor.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Distributor.retail_shop_id]).where(Distributor.id == self.distributor_id).as_scalar()

    @hybrid_property
    def retail_shop_name(self):
        return self.distributor.retail_shop.name

    @retail_shop_name.expression
    def retail_shop_name(self):
        return select([Distributor.retail_shop_name]).where(Distributor.id == self.distributor_id).as_scalar()

    @hybrid_property
    def distributor_name(self):
        return self.distributor.name

    @distributor_name.expression
    def distributor_name(self):
        return select([Distributor.name]).where(Distributor.id == self.distributor_id).as_scalar()


class ProductType(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(80), unique=True, index=True)
    description = db.Column(db.TEXT())
    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True)


class Tag(BaseMixin, db.Model, ReprMixin):
    name = db.Column(db.String(55), unique=False, nullable=False, index=True)
    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True, nullable=False)

    products = db.relationship('Product', back_populates='tags', secondary='product_tag')
    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False, backref='tags')

    UniqueConstraint(name, retail_shop_id)


class ProductTag(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['tag_id', 'product_id']

    tag_id = db.Column(UUID, db.ForeignKey('tag.id'), index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True)

    tag = db.relationship('Tag', foreign_keys=[tag_id])
    product = db.relationship('Product', foreign_keys=[product_id])

    UniqueConstraint(tag_id, product_id)

    @hybrid_property
    def retail_shop_id(self):
        return self.product.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Product.retail_shop_id]).where(Product.id == self.product_id).as_scalar()


class BrandDistributor(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['brand_id', 'distributor_id']

    brand_id = db.Column(UUID, db.ForeignKey('brand.id'), index=True, nullable=False)
    distributor_id = db.Column(UUID, db.ForeignKey('distributor.id'), index=True, nullable=False)

    brand = db.relationship('Brand', foreign_keys=[brand_id])
    distributor = db.relationship('Distributor', foreign_keys=[distributor_id])

    UniqueConstraint(brand_id, distributor_id)

    @hybrid_property
    def retail_shop_id(self):
        return self.brand.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Brand.retail_shop_id]).where(Brand.id == self.brand_id).as_scalar()


class ProductDistributor(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['distributor_id', 'product_id']

    distributor_id = db.Column(UUID, db.ForeignKey('distributor.id'), index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True)

    distributor = db.relationship('Distributor', foreign_keys=[distributor_id])
    product = db.relationship('Product', foreign_keys=[product_id])

    UniqueConstraint(distributor_id, product_id)

    @hybrid_property
    def retail_shop_id(self):
        return self.product.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Product.retail_shop_id]).where(Product.id == self.product_id).as_scalar()


class Product(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(127), unique=False, nullable=False, index=True)
    min_stock = db.Column(db.SmallInteger, nullable=False)
    auto_discount = db.Column(db.FLOAT(precision=2), default=0, nullable=False)
    description = db.Column(db.JSON(), nullable=True)
    sub_description = db.Column(db.Text(), nullable=True)
    is_disabled = db.Column(db.Boolean(), default=False)
    default_quantity = db.Column(db.Float(precision=2), default=1)
    quantity_label = db.Column(db.Enum('KG', 'GM', 'MG', 'L', 'ML', 'TAB', 'SYRUP', 'OTH', 'TAB', 'ML', 'CAP', 'INJ',
                                       'BOTTLE', 'VAIL', 'KIT', 'STRIP', 'OTHER', 'PACK', 'SET', 'LTR', 'SACHET',
                                       'PILLS', 'SYRINGE', 'SYRUP', 'ROLL', name='varchar'),
                               default='OTH', nullable=True)
    is_loose = db.Column(db.Boolean(), default=False)
    barcode = db.Column(db.String(13), nullable=True)

    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True, nullable=False)
    brand_id = db.Column(UUID, db.ForeignKey('brand.id'), index=True, nullable=False)

    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False, back_populates='products')
    taxes = db.relationship('Tax', back_populates='products', secondary='product_tax')
    tags = db.relationship('Tag', back_populates='products', secondary='product_tag')
    brand = db.relationship('Brand', foreign_keys=[brand_id], uselist=False, back_populates='products')

    stocks = db.relationship('Stock', uselist=True, cascade="all, delete-orphan", lazy='dynamic')
    # distributors = db.relationship('Distributor', back_populates='products', secondary='product_distributor')
    combos = db.relationship('Combo', back_populates='products', secondary='combo_product')
    salts = db.relationship('Salt', back_populates='products', secondary='product_salt')
    add_ons = db.relationship('AddOn', back_populates='products', secondary='product_add_on')

    UniqueConstraint('barcode', 'retail_shop_id', 'bar_retail_un')

    @hybrid_property
    def available_stock(self):
        return self.stocks.filter(Stock.is_sold != True, Stock.expired == False)\
            .with_entities(func.coalesce(func.Sum(Stock.units_purchased), 0)-func.coalesce(func.Sum(Stock.units_sold),
                                                                                           0)).scalar()

    @hybrid_property
    def available_stocks(self):
        return self.stocks.filter(and_(or_(Stock.is_sold != True), Stock.expired == False)).all()

    @available_stock.expression
    def available_stock(cls):
        return select([func.coalesce(func.Sum(Stock.units_purchased), 0)-func.coalesce(func.Sum(Stock.units_sold), 0)])\
            .where(and_(or_(Stock.is_sold != True), Stock.product_id == cls.id)).as_scalar()

    @hybrid_property
    def mrp(self):
        mrp = self.stocks.filter(or_(Stock.is_sold != True))\
            .with_entities(Stock.selling_amount).order_by(Stock.id).first()
        return mrp[0] if mrp else 0

    @hybrid_property
    def similar_products(self):
        if len(self.salts):
            return [i[0] for i in Product.query.with_entities(Product.id)
                    .join(ProductSalt, and_(ProductSalt.product_id == Product.id))
                    .filter(ProductSalt.salt_id.in_([i.id for i in self.salts])).group_by(Product.id)
                    .having(func.Count(func.Distinct(ProductSalt.salt_id)) == len(self.salts)).all()]
        return []

    @hybrid_property
    def last_purchase_amount(self):
        return self.stocks.order_by(desc(Stock.purchase_date)).first().purchase_amount

    @hybrid_property
    def last_selling_amount(self):
        return self.stocks.order_by(desc(Stock.purchase_date)).first().selling_amount

    @hybrid_property
    def stock_required(self):
        return abs(self.min_stock - self.available_stock)

    @stock_required.expression
    def stock_required(self):
        return self.min_stock - self.available_stock

    @hybrid_property
    def is_short(self):
        return self.min_stock >= self.available_stock

    @hybrid_property
    def product_name(self):
        return self.name

    @hybrid_property
    def distributors(self):
        return self.brand.distributors.all()

    @hybrid_property
    def brand_name(self):
        return self.brand.name

    @brand_name.expression
    def brand_name(self):
        return select([Brand.name]).where(Brand.id == self.brand_id).as_scalar()


class Salt(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(127), unique=True, nullable=False, index=True)
    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True, nullable=False)

    products = db.relationship('Product', back_populates='salts', secondary='product_salt')
    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id], uselist=False)

    UniqueConstraint(name, retail_shop_id)


class ProductSalt(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['salt_id', 'product_id']

    salt_id = db.Column(UUID, db.ForeignKey('salt.id'), index=True, nullable=False)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True, nullable=False)

    salt = db.relationship('Salt', foreign_keys=[salt_id])
    product = db.relationship('Product', foreign_keys=[product_id])

    UniqueConstraint(salt_id, product_id)

    @hybrid_property
    def retail_shop_id(self):
        return self.product.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Product.retail_shop_id]).where(Product.id == self.product_id).as_scalar()


class Stock(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['id', 'purchase_date']

    purchase_amount = db.Column(db.Float(precision=2), nullable=False, default=0)
    selling_amount = db.Column(db.Float(precision=2), nullable=False, default=0)
    units_purchased = db.Column(db.SmallInteger, nullable=False, default=1)
    batch_number = db.Column(db.String(25), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    is_sold = db.Column(db.Boolean(), default=False, index=True)
    default_stock = db.Column(db.Boolean, default=False, nullable=True)

    distributor_bill_id = db.Column(UUID, db.ForeignKey('distributor_bill.id'), nullable=True, index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), nullable=False, index=True)

    distributor_bill = db.relationship('DistributorBill', single_parent=True, back_populates='purchased_items')
    product = db.relationship('Product', single_parent=True, foreign_keys=product_id)
    order_items = db.relationship('Item', uselist=True, back_populates='stock', lazy='dynamic')

    @hybrid_property
    def units_sold(self):

        total_sold = self.order_items.with_entities(func.Sum(Item.quantity))\
            .filter(Item.stock_id == self.id).scalar()
        if total_sold:
            if total_sold >= self.units_purchased and not self.is_sold:
                self.is_sold = True
                db.session.commit()
            return total_sold
        else:
            return 0

    @units_sold.expression
    def units_sold(cls):
        return select([func.coalesce(func.Sum(Item.quantity), 0)]).where(Item.stock_id == cls.id).as_scalar()

    @hybrid_property
    def product_name(self):
        return self.product.name

    @product_name.expression
    def product_name(self):
        return select([Product.name]).where(Product.id == self.product_id).as_scalar()

    @hybrid_property
    def retail_shop_id(self):
        return self.product.retail_shop_id

    @retail_shop_id.expression
    def retail_shop_id(self):
        return select([Product.retail_shop_id]).where(Product.id == self.product_id).as_scalar()

    @hybrid_property
    def expired(self):
        return self.expiry_date is not None and self.expiry_date < datetime.now().date()

    @expired.expression
    def expired(self):
        return and_(or_(self.is_sold != True), func.coalesce(self.expiry_date, datetime.now().date())
                    < datetime.now().date()).label('expired')

    @hybrid_property
    def distributor_id(self):
        return self.distributor_bill.distributor_id

    @distributor_id.expression
    def distributor_id(self):
        return select([DistributorBill.distributor_id]).where(DistributorBill.id == self.distributor_bill_id).as_scalar()

    @hybrid_property
    def distributor_name(self):
        return self.distributor_bill.distributor.name

    @distributor_name.expression
    def distributor_name(self):
        return select([Distributor.name]).where(and_(DistributorBill.id == self.distributor_bill_id,
                                                     Distributor.id == DistributorBill.distributor_id)).as_scalar()

    @hybrid_property
    def purchase_date(self):
        if self.distributor_bill_id:
            return self.distributor_bill.purchase_date
        return None

    @purchase_date.expression
    def purchase_date(cls):
        return select([DistributorBill.purchase_date]).where(DistributorBill.id == cls.distributor_bill_id).as_scalar()

    @hybrid_property
    def quantity_label(self):
        return self.product.quantity_label

    @quantity_label.expression
    def quantity_label(cls):
        return select([Product.quantity_label]).where(Product.id == cls.product_id).as_scalar()

    @hybrid_property
    def brand_name(self):
        return self.product.brand.name

    @brand_name.expression
    def brand_name(self):
        return select([Brand.name]).where(and_(Product.id == self.product_id,
                                                     Brand.id == Product.brand_id)).as_scalar()


class Combo(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(55), nullable=False, index=True)
    products = db.relationship('Product', back_populates='combos', secondary='combo_product')


class ComboProduct(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['combo_id', 'product_id']

    combo_id = db.Column(UUID, db.ForeignKey('combo.id'), index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True)

    combo = db.relationship('Combo', foreign_keys=[combo_id])
    product = db.relationship('Product', foreign_keys=[product_id])


class AddOn(BaseMixin, db.Model, ReprMixin):

    name = db.Column(db.String(127), unique=True, nullable=False, index=True)
    retail_shop_id = db.Column(UUID, db.ForeignKey('retail_shop.id', ondelete='CASCADE'), index=True)

    products = db.relationship('Product', back_populates='add_ons', secondary='product_add_on')


class ProductAddOn(BaseMixin, db.Model, ReprMixin):

    __repr_fields__ = ['add_on_id', 'product_id']

    add_on_id = db.Column(UUID, db.ForeignKey('add_on.id'), index=True)
    product_id = db.Column(UUID, db.ForeignKey('product.id'), index=True)

    add_on = db.relationship('AddOn', foreign_keys=[add_on_id])
    product = db.relationship('Product', foreign_keys=[product_id])
