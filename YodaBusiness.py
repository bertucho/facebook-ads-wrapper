from facebookads.api import FacebookAdsApi, FacebookRequest
from facebookads import objects
from facebookads.adobjects.abstractcrudobject import AbstractCrudObject
from facebookads.api import FacebookRequest
from facebookads.typechecker import TypeChecker
from facebookads.adobjects.objectparser import ObjectParser
from .YodaAccount import YodaAccount
from .YodaProject import Project
from . import utils
from facebookads.objects import (
    Business,
    AdUser,
    Campaign,
    AdSet,
    Ad,
    AdCreative,
    AdImage,
    TargetingSpecsField,
    AdAccount
)

class YodaBusiness(Business):

    def __init__(self, fbid=None, parent_id=None, api=None):
        self._isYodaBusiness = True
        super().__init__(fbid, parent_id, api)


    class Roles:
        manager = 'MANAGER'
        content_creator = 'CONTENT_CREATOR'
        moderator = 'MODERATOR'
        advertiser = 'ADVERTISER'
        insights_analyst = 'INSIGHTS_ANALYST'


    def createAdAccount(self, name, funding_id, currency="EUR", timezone_id=1, partner="NONE", end_advertiser="NONE", media_agency="NONE"):
        params = {
            'currency': currency,
            'end_advertiser': end_advertiser,
            'funding_id': funding_id,
            'media_agency': media_agency,
            'name': name,
            'partner': partner,
            'timezone_id': timezone_id
        }
        resp = self.create_ad_account(params=params)
        return YodaAccount(resp.get_id_assured())


    def createAccountStructure(self, acc, overwrite=False):
        ads = acc['ads']
        bid_amount = acc['bid_amount']
        country_code = acc['country_code']
        currency = acc['currency']
        end_date = acc['end_date']
        funding_id = acc['funding_id']
        keywords = acc['keywords']
        name = acc['name']
        page_id = acc['page_id']
        spend_cap = acc['spend_cap']
        start_date = acc['start_date']

        # Si existe cuenta con el mismo nombre la sobrescribe dependiendo de argumento 'overwrite'
        account = self.getAccountByName(name)
        if account and overwrite==False:
            raise NameError("Ya existe una cuenta con ese nombre")
        # Si no existe la crea
        if not account:
            account = self.createAdAccount(name, funding_id, currency)
        print(account)
        account.assignAdAccount(self.get_id_assured())
        #account.setSpendCap(spend_cap)
        campaign = account.createCampaign(name)
        print(campaign)
        #get interests {id, name} by list of keywords
        interests = utils.getInterests(keywords)
        adset = account.createAdSet(campaign, name, bid_amount, start_date, end_date, country_code, daily_budget=spend_cap*100, interests=interests)

        remoteAds = []
        for ad in ads:
            adImage = account.createAdImage(ad['image_filename'])
            crea = account.createAdCreative(name,
                adImage.get_hash(),
                ad['message'],
                ad['headline'],
                ad['description'],
                ad['caption'],
                ad['url'],
                page_id)
            remoteAd = account.createAd(name, adset, crea, objects.Ad.Status.paused)
            remoteAds.append(remoteAd)
        for ad in remoteAds:
            print(ad)


    def getAccountByName(self, name):
        allAccounts = self.get_owned_ad_accounts({AdAccount.Field.name})
        account = None
        variasOcurrencias = False
        for acc in allAccounts:
            if acc[AdAccount.Field.name] == name:
                if account:
                    raise LookupError("Hay más de una cuenta con el mismo nombre")
                account = acc
        if not account:
            return None
        return YodaAccount(account.get_id_assured())


    def claimPage(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
            'page_id': 'string',
            'access_type': 'access_type_enum',
            'user': 'string',
            'permitted_roles': 'list<permitted_roles_enum>'
        }
        enums = {
            'access_type_enum': [
                'OWNER',
                'AGENCY'
            ],
            'permitted_roles_enum': self.Roles.__dict__.values()
        }
        request = FacebookRequest(
            node_id=self['id'],
            method='POST',
            endpoint='/pages',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=AbstractCrudObject,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def requestPageAccess(self, page_id):
        params = {
            'page_id': page_id,
            'access_type': 'AGENCY',
            'permitted_roles': ['ADVERTISER', 'INSIGHTS_ANALYST'],
            'user': utils.getCurrentAccountId()
        }
        resp = self.claimPage(params=params)
        return resp


    def assign_people_to_page(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
            'business': 'string',
            'role': 'role_enum',
            'user': 'string',
            'page_id': 'string'
        }
        enums = {
            'role_enum': self.Roles.__dict__.values()
        }
        if 'page_id' not in params:
            raise AttributeError("Debes especificar 'page_id' como parámetro")
        request = FacebookRequest(
            node_id=params['page_id'],
            method='POST',
            endpoint='/userpermissions',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=AbstractCrudObject,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def assignPage(self, page_id):
        params = {
            'business': self.get_id_assured(),
            'role': self.Roles.advertiser,
            'user': utils.getCurrentAccountId(),
            'page_id': page_id
        }
        resp = self.assign_people_to_page(params=params)
        return resp


    def checkPagesStatus(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
        }
        enums = {
        }
        request = FacebookRequest(
            node_id=self.get_id_assured(),
            method='GET',
            endpoint='/pages',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=AbstractCrudObject,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def create_project(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
            'name': 'string'
        }
        enums = {
        }
        request = FacebookRequest(
            node_id=self.get_id_assured(),
            method='POST',
            endpoint='/businessprojects',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=Project,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def createProject(self, name):
        return self.create_project(params={'name': name})


    def get_projects(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
        }
        enums = {
        }
        request = FacebookRequest(
            node_id=self.get_id_assured(),
            method='GET',
            endpoint='/businessprojects',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=Project,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def getProjectByName(self, name):
        projects = self.get_projects()
        project = None
        for proj in projects:
            if proj['name'] == name:
                if project:
                    raise LookupError("Hay más de una cuenta con el mismo nombre")
                project = proj
        return project


    def create_page(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
            'about': 'string',
            'address': 'string',
            'category': 'int',
            'category_enum': 'string',
            'category_list': 'list<string>',
            'city_id': 'string',
            'coordinates': 'Object',
            'cover_photo': 'Object',
            'description': 'string',
            'ignore_coordinate_warnings': 'boolean',
            'location': 'Object',
            'name': 'string',
            'phone': 'string',
            'picture': 'string',
            'website': 'string',
            'zip': 'string'
        }
        enums = {
        }
        request = FacebookRequest(
            node_id=utils.getCurrentAccountId(),
            method='POST',
            endpoint='/accounts',
            api=self._api,
            param_checker=TypeChecker(param_types, enums),
            target_class=AbstractCrudObject,
            api_type='EDGE',
            response_parser=ObjectParser(target_class=AbstractCrudObject),
        )
        request.add_params(params)
        request.add_fields(fields)

        if batch is not None:
            request.add_to_batch(batch)
            return request
        elif pending:
            return request
        else:
            self.assure_call()
            return request.execute()


    def createPage(self, name, category_id):
        params = {
            'name': name,
            'category_enum': category_id
        }
        return self.create_page(params=params)