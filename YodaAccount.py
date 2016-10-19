from facebookads.api import FacebookAdsApi
from facebookads import objects
from facebookads.api import FacebookRequest
from facebookads.typechecker import TypeChecker
from facebookads.adobjects.objectparser import ObjectParser
from facebookads.adobjects.abstractcrudobject import AbstractCrudObject
from facebookads.objects import (
    AdUser,
    Campaign,
    AdSet,
    Ad,
    AdCreative,
    AdImage,
    Insights,
    TargetingSpecsField,
    AdAccount
)
from facebookads.adobjects.adcreativelinkdata import AdCreativeLinkData
from facebookads.adobjects.adcreativeobjectstoryspec import AdCreativeObjectStorySpec
from facebookads.adobjects.targetinggeolocation import TargetingGeoLocation
from .Exceptions import InvalidObject
from . import utils

class YodaAccount(AdAccount):

    def __init__(self, fbid=None, parent_id=None, api=None):
        self._isYodaAccount = True
        super().__init__(fbid, parent_id, api)


    def createCampaign(self, name, spend_cap=10000):

        params = {
            Campaign.Field.name : name,
            Campaign.Field.status : Campaign.Status.paused,
            Campaign.Field.objective : Campaign.Objective.link_clicks,
            Campaign.Field.spend_cap : spend_cap
        }

        campaign = self.create_campaign(params = params)
        return campaign


    def getCampaignByName(self, name):
        allCampaigns = self.get_campaigns({Campaign.Field.name})
        campaign = None
        variasOcurrencias = False
        for camp in allCampaigns:
            if camp[Campaign.Field.name] == name:
                if campaign:
                    raise LookupError("Hay más de una campaña con el mismo nombre")
                campaign = camp
        return campaign



    def createAdSet(
        self,
        campaign, #objeto Campaign
        name,
        bid_amount,
        start_time,
        end_time, # Por defecto no terminaria
        country_code,
        daily_budget=50000,
        optimization_goal=AdSet.OptimizationGoal.link_clicks,
        status=AdSet.Status.paused,
        interests=[], #lista de objetos con id y nombre de cada interes
        age_min=None,
        age_max=None,
        genders=None
    ):
        targeting = {}
        targeting[TargetingSpecsField.geo_locations] = {
            TargetingGeoLocation.Field.countries: [country_code]
        }
        if age_max:
            targeting[TargetingSpecsField.age_max] = age_max
        if age_min:
            targeting[TargetingSpecsField.age_min] = age_min
        if genders:
            targeting[TargetingSpecsField.genders] = genders
        if interests:
            targeting[TargetingSpecsField.interests] = interests

        params = {}
        params[AdSet.Field.campaign_id] = campaign.get_id_assured()
        params[AdSet.Field.start_time] = start_time
        params[AdSet.Field.end_time] = end_time
        params[AdSet.Field.daily_budget] = daily_budget
        params[AdSet.Field.bid_amount] = bid_amount
        params[AdSet.Field.name] = name
        params[AdSet.Field.billing_event] = AdSet.BillingEvent.link_clicks
        params[AdSet.Field.optimization_goal] = optimization_goal
        params[AdSet.Field.status] = status
        params[AdSet.Field.targeting] = targeting

        response = self.create_ad_set(params=params)
        return response


    def createAdImage(self, filepath):
        image = AdImage()
        return image.api_create(parent_id=self.get_id_assured(),params={AdImage.Field.filename: filepath})


    def createAdCreative(self, name, imageHash, message, headline, description, caption, url, pageId):

        linkData = AdCreativeLinkData()
        linkData[AdCreativeLinkData.Field.message] = message
        linkData[AdCreativeLinkData.Field.link] = url
        linkData[AdCreativeLinkData.Field.caption] = caption
        linkData[AdCreativeLinkData.Field.description] = description
        linkData[AdCreativeLinkData.Field.name] = headline
        linkData[AdCreativeLinkData.Field.image_hash] = imageHash

        objectStorySpec = AdCreativeObjectStorySpec()
        objectStorySpec[AdCreativeObjectStorySpec.Field.page_id] = pageId
        objectStorySpec[AdCreativeObjectStorySpec.Field.link_data] = linkData

        params = {
            AdCreative.Field.image_hash: imageHash,
            AdCreative.Field.body: description,
            AdCreative.Field.title: headline,
            AdCreative.Field.actor_id: pageId,
            AdCreative.Field.object_story_spec: objectStorySpec,
            AdCreative.Field.name: name,
        }
        adCrea = AdCreative()
        return adCrea.api_create(parent_id=self.get_id_assured(), params=params)


    def createAd(self, name, adset, adcrea, status):
        ad = Ad()
        params = {
            Ad.Field.name: name,
            Ad.Field.adset_id: adset.get_id_assured(),
            Ad.Field.creative: adcrea,
            Ad.Field.redownload: True,
            Ad.Field.status: status
        }
        ad.api_create(parent_id=self.get_id_assured(), params=params)
        return ad


    def setSpendCap(self, spendCap):
        resp = self.api_update(params={AdAccount.Field.spend_cap: spendCap})
        return resp


    def getAccountInfo(self):
        fields = [
            AdAccount.Field.id,
            AdAccount.Field.account_id,
            AdAccount.Field.account_status,
            AdAccount.Field.amount_spent,
            AdAccount.Field.balance,
            AdAccount.Field.capabilities,
            AdAccount.Field.created_time,
            AdAccount.Field.currency,
            AdAccount.Field.disable_reason,
            AdAccount.Field.end_advertiser,
            AdAccount.Field.funding_source,
            AdAccount.Field.funding_source_details,
            AdAccount.Field.io_number,
            AdAccount.Field.min_campaign_group_spend_cap,
            AdAccount.Field.min_daily_budget,
            AdAccount.Field.name,
            AdAccount.Field.owner,
            AdAccount.Field.business,
            AdAccount.Field.partner,
            AdAccount.Field.spend_cap,
            AdAccount.Field.timezone_id,
            AdAccount.Field.timezone_name,
            AdAccount.Field.timezone_offset_hours_utc,
            AdAccount.Field.user_role
        ]
        return self.api_get(fields=fields)


    def getAdSetsRecommendations(self):
        adsets = self.get_ad_sets()
        recommendations = []
        for adset in adsets:
            recommendations.append(adset.api_get(fields={"recommendations"}))
        return recommendations


    def assign_user_to_ad_account(self, fields=None, params=None, batch=None, pending=False):
        param_types = {
            'business': 'string',
            'role': 'role_enum',
            'user': 'string',
        }
        enums = {
            'role_enum': [
                'ADMIN',
                'GENERAL_USER',
                'REPORTS_ONLY'
            ],
        }
        request = FacebookRequest(
            node_id=self['id'],
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


    def assignAdAccount(self, business_id):
        params = {
            'business': business_id,
            'role': 'ADMIN',
            'user': utils.getCurrentAccountId()
        }
        resp = self.assign_user_to_ad_account(params=params)
        return resp


    def assignUser(self, business_id, act_id):
        params = {
            'business': business_id,
            'role': 'ADMIN',
            'user': act_id
        }
        resp = self.assign_user_to_ad_account(params=params)
        return resp


    def getCampaignInsights(self, campaign):
        params = {
            'date_preset': Campaign.DatePreset.last_7_days,
            'fields': [Insights.Field.impressions, Insights.Field.ad_id, Insights.Field.cpc, Insights.Field.objective ]
        }
        fields = [
            'campaign_name',
            'adset_name',
            'adset_id',
            'impressions',
            'website_clicks',
            'app_store_clicks',
            'deeplink_clicks',
            'spend',
            'reach',
            'actions',
            'action_values'
        ]
        return campaign.get_insights(params=params, fields=fields)