from src import BaseView, AssociationView
from .resources import BrandResource, DistributorBillResource, DistributorResource, ProductResource, \
    ProductTaxResource, StockResource, TaxResource, TagResource, ComboResource, AddOnResource, SaltResource
from src import api


@api.register()
class ProductView(BaseView):
    resource = ProductResource


@api.register()
class TagView(BaseView):
    resource = TagResource


@api.register()
class StockView(BaseView):
    resource = StockResource


@api.register()
class DistributorView(BaseView):
    resource = DistributorResource


@api.register()
class DistributorBillView(BaseView):
    resource = DistributorBillResource


@api.register()
class TaxView(BaseView):
    resource = TaxResource


@api.register()
class BrandView(BaseView):
    resource = BrandResource


@api.register()
class ComboView(BaseView):
    resource = ComboResource


@api.register()
class AddOnView(BaseView):
    resource = AddOnResource


@api.register()
class SaltView(BaseView):
    resource = SaltResource


@api.register()
class ProductTaxAssociationView(AssociationView):

    resource = ProductTaxResource
