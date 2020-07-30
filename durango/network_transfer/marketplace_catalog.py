import sys
import io
import json
from jsonobject import *


class _Image(JsonObject):
    BackgroundColor = StringProperty()
    Caption = StringProperty()
    FileSizeInBytes = IntegerProperty()
    ForegroundColor = StringProperty()
    Height = IntegerProperty()
    ImagePositionInfo = StringProperty()
    ImagePurpose = StringProperty()
    UnscaledImageSHA256Hash = StringProperty()
    Uri = StringProperty()
    Width = IntegerProperty()


class _SearchTitle(JsonObject):
    SearchTitleString = StringProperty()
    SearchTitleType = StringProperty()


class PreviewImage(JsonObject):
    # BackgroundColor = None
    Caption = StringProperty()
    FileSizeInBytes = IntegerProperty()
    # ForegroundColor = None
    Height = IntegerProperty()
    # ImagePositionInfo = None
    ImagePurpose = StringProperty()
    UnscaledImageSHA256Hash = StringProperty()
    Uri = StringProperty()
    Width = IntegerProperty()


class _Video(JsonObject):
    AudioEncoding = StringProperty()
    Caption = StringProperty()
    FileSizeInBytes = IntegerProperty()
    Height = IntegerProperty()
    PreviewImage = DictProperty(PreviewImage)
    SortOrder = IntegerProperty()
    Uri = StringProperty()
    VideoEncoding = StringProperty()
    VideoPositionInfo = StringProperty()
    VideoPurpose = StringProperty()
    Width = IntegerProperty()


class _ContentRating(JsonObject):
    InteractiveElements = ListProperty(str)
    RatingDescriptors = ListProperty(str)
    RatingDisclaimers = ListProperty(str)
    RatingId = StringProperty()
    RatingSystem = StringProperty()


class _UsageData(JsonObject):
    AggregateTimeSpan = StringProperty()
    AverageRating = FloatProperty()
    PlayCount = FloatProperty()
    PurchaseCount = FloatProperty()
    RatingCount = IntegerProperty()
    RentalCount = FloatProperty()
    TrialCount = FloatProperty()


class ValidationData(JsonObject):
    PassedValidation = BooleanProperty()
    RevisionId = StringProperty()
    ValidationResultUri = StringProperty()


class _AlternateId(JsonObject):
    IdType = StringProperty()
    Value = StringProperty()


class _Attribute(JsonObject):
    # ApplicablePlatforms = None
    # Group = None
    Maximum = IntegerProperty()
    Minimum = IntegerProperty()
    Name = StringProperty()


class _AllowedPlatform(JsonObject):
    MaxVersion = IntegerProperty()
    MinVersion = IntegerProperty()
    PlatformName = StringProperty()


class ClientCondition(JsonObject):
    AllowedPlatforms = ListProperty(_AllowedPlatform)


class Condition(JsonObject):
    ClientConditions = DictProperty(ClientCondition)
    EndDate = StringProperty()
    ResourceSetIds = ListProperty(str)
    StartDate = StringProperty()


class FulfillmentData(JsonObject):
    # Content = None
    PackageFamilyName = StringProperty()
    ProductId = StringProperty()
    SkuId = StringProperty()
    WuBundleId = StringProperty()
    WuCategoryId = StringProperty()


class HardwareProperty(JsonObject):
    MinimumGraphics = StringProperty()
    MinimumHardware = ListProperty(str)
    MinimumProcessor = StringProperty()
    RecommendedGraphics = StringProperty()
    RecommendedHardware = ListProperty(str)
    RecommendedProcessor = StringProperty()

class _Application(JsonObject):
    ApplicationId = StringProperty()
    DeclarationOrder = IntegerProperty()
    Extensions = ListProperty(str)


class _FrameworkDependency(JsonObject):
    MaxTested = IntegerProperty()
    MinVersion = IntegerProperty()
    PackageIdentity = StringProperty()


class _PlatformDependency(JsonObject):
    MaxTested = IntegerProperty()
    MinVersion = IntegerProperty()
    PlatformName = StringProperty()


class _Package(JsonObject):
    Applications = ListProperty(_Application)
    Architectures = ListProperty(str)
    Capabilities = ListProperty(str)
    ContentId = StringProperty()
    DeviceCapabilities = ListProperty(str)
    DriverDependencies = ListProperty(str)
    ExperienceIds = ListProperty(str)
    FrameworkDependencies = ListProperty(_FrameworkDependency)
    FulfillmentData = DictProperty(FulfillmentData)
    HardwareDependencies = ListProperty(str)
    HardwareRequirements = ListProperty(str)
    Hash = StringProperty()
    HashAlgorithm = StringProperty()
    IsStreamingApp = BooleanProperty()
    KeyId = StringProperty()
    Languages = ListProperty(str)
    # MainPackageFamilyNameForDlc = None
    MaxDownloadSizeInBytes = IntegerProperty()
    MaxInstallSizeInBytes = IntegerProperty()
    # PackageDownloadUris = None
    PackageFamilyName = StringProperty()
    PackageFormat = StringProperty()
    PackageFullName = StringProperty()
    PackageId = StringProperty()
    PackageRank = IntegerProperty()
    PackageUri = StringProperty()
    PlatformDependencies = ListProperty(_PlatformDependency)
    PlatformDependencyXmlBlob = StringProperty()
    ResourceId = StringProperty()
    Version = StringProperty()


class _Affirmation(JsonObject):
    AffirmationId = StringProperty()
    AffirmationProductId = StringProperty()
    Description = StringProperty()


class _Remediation(JsonObject):
    Description = StringProperty()
    RemediationId = StringProperty()


class EligibilityProperty(JsonObject):
    Affirmations = ListProperty(_Affirmation)
    Remediations = ListProperty(_Remediation)


class PIFilter(JsonObject):
    ExclusionProperties = ListProperty(str)
    InclusionProperties = ListProperty(str)


class Price(JsonObject):
    CurrencyCode = StringProperty()
    IsPIRequired = BooleanProperty()
    ListPrice = FloatProperty()
    MSRP = FloatProperty()
    TaxType = StringProperty()
    WholesaleCurrencyCode = StringProperty()
    WholesalePrice = FloatProperty()


class OrderManagementData(JsonObject):
    GrantedEntitlementKeys = ListProperty(str)
    PIFilter = DictProperty(PIFilter)
    Price = DictProperty(Price)


class Property(JsonObject):
    Attributes = ListProperty(_Attribute)
    CanInstallToSDCard = BooleanProperty()
    Categories = ListProperty(str)
    Category = StringProperty()
    HasAddOns = BooleanProperty()
    IsAccessible = BooleanProperty()
    IsDemo = BooleanProperty()
    IsLineOfBusinessApp = BooleanProperty()
    IsPublishedToLegacyWindowsPhoneStore = BooleanProperty()
    IsPublishedToLegacyWindowsStore = BooleanProperty()
    # OwnershipType = None
    PackageFamilyName = StringProperty()
    PackageIdentityName = StringProperty()
    PdpBackgroundColor = StringProperty()
    ProductGroupId = StringProperty()
    ProductGroupName = StringProperty()
    PublisherCertificateName = StringProperty()
    PublisherId = StringProperty()
    RevisionId = StringProperty()
    # SkuDisplayGroups = None
    # Subcategory = None
    XboxLiveTier = StringProperty()
    AdditionalIdentifiers = ListProperty(str)
    BundledSkus = ListProperty(str)
    # DisplayPhysicalStoreInventory = None
    # EarlyAdopterEnrollmentUrl = None
    FulfillmentData = DictProperty(FulfillmentData)
    # FulfillmentType = None
    HardwareProperties = DictProperty(HardwareProperty)
    HardwareRequirements = ListProperty(str)
    HardwareWarningList = ListProperty(str)
    HasThirdPartyIAPs = BooleanProperty()
    InstallationTerms = StringProperty()
    IsBundle = BooleanProperty()
    IsPreOrder = BooleanProperty()
    IsRepurchasable = BooleanProperty()
    IsTrial = BooleanProperty()
    LastUpdateDate = StringProperty()
    Packages = ListProperty(_Package)
    # SkuDisplayGroupIds = None
    SkuDisplayRank = IntegerProperty()
    VersionString = StringProperty()
    VisibleToB2BServiceIds = ListProperty(str)
    XboxXPA = BooleanProperty()
    OriginalReleaseDate = StringProperty()


class _Availability(JsonObject):
    Actions = ListProperty(str)
    AlternateIds = ListProperty(_AlternateId)
    AvailabilityASchema = StringProperty()
    AvailabilityBSchema = StringProperty()
    AvailabilityId = StringProperty()
    Conditions = DictProperty(Condition)
    DisplayRank = IntegerProperty()
    LastModifiedDate = StringProperty()
    Markets = ListProperty(str)
    OrderManagementData = DictProperty(OrderManagementData)
    Properties = DictProperty(Property)
    RemediationRequired = BooleanProperty()
    SkuId = StringProperty()


class LegalText(JsonObject):
    AdditionalLicenseTerms = StringProperty()
    Copyright = StringProperty()
    CopyrightUri = StringProperty()
    PrivacyPolicy = StringProperty()
    PrivacyPolicyUri = StringProperty()
    Tou = StringProperty()
    TouUri = StringProperty()


class _LocalizedProperty(JsonObject):
    DeveloperName = StringProperty()
    EligibilityProperties = DictProperty(EligibilityProperty)
    Franchises = ListProperty(str)
    Images = ListProperty(_Image)
    Language = StringProperty()
    Markets = ListProperty(str)
    ProductDescription = StringProperty()
    ProductDisplayRanks = ListProperty(str)
    ProductTitle = StringProperty()
    PublisherName = StringProperty()
    PublisherWebsiteUri = StringProperty()
    # RenderGroupDetails = None
    SearchTitles = ListProperty(_SearchTitle)
    ShortDescription = StringProperty()
    ShortTitle = StringProperty()
    SortTitle = StringProperty()
    SupportUri = StringProperty()
    Videos = ListProperty(_Video)
    VoiceTitle = StringProperty()
    Contributors = ListProperty(str)
    # DeliveryDateOverlay = None
    # DisplayPlatformProperties = None
    Features = ListProperty(str)
    LegalText = DictProperty(LegalText)
    MinimumNotes = StringProperty()
    RecommendedNotes = StringProperty()
    ReleaseNotes = StringProperty()
    SkuButtonTitle = StringProperty()
    SkuDescription = StringProperty()
    SkuDisplayRank = ListProperty(str)
    SkuTitle = StringProperty()
    # TextResources = None


class RelatedProduct(JsonObject):
    RelationshipType = StringProperty()
    RelatedProductId = StringProperty()


class _MarketProperty(JsonObject):
    # BundleConfig = None
    ContentRatings = ListProperty(_ContentRating)
    Markets = ListProperty(str)
    MinimumUserAge = IntegerProperty()
    OriginalReleaseDate = DateTimeProperty()
    RelatedProducts = ListProperty(RelatedProduct)
    UsageData = ListProperty(_UsageData)
    # FirstAvailableDate = None
    # PackageIds = None
    SupportedLanguages = ListProperty(str)


class Sku(JsonObject):
    LastModifiedDate = StringProperty()
    LocalizedProperties = ListProperty(_LocalizedProperty)
    MarketProperties = ListProperty(_MarketProperty)
    ProductId = StringProperty()
    Properties = DictProperty(Property)
    # RecurrencePolicy = None
    SkuASchema = StringProperty()
    SkuBSchema = StringProperty()
    SkuId = StringProperty()
    SkuType = StringProperty()
    # SubscriptionPolicyId = None


class _DisplaySkuAvailability(JsonObject):
    Availabilities = ListProperty(_Availability)
    Sku = DictProperty(Sku)


class Product(JsonObject):
    AlternateIds = ListProperty(_AlternateId)
    DisplaySkuAvailabilities = ListProperty(_DisplaySkuAvailability)
    DomainDataVersion = StringProperty()
    IngestionSource = StringProperty()
    IsMicrosoftProduct = BooleanProperty()
    IsSandboxedProduct = BooleanProperty()
    LastModifiedDate = DateTimeProperty()
    LocalizedProperties = ListProperty(_LocalizedProperty)
    MarketProperties = ListProperty(_MarketProperty)
    MerchandizingTags = ListProperty(str)
    PartD = StringProperty()
    PreferredSkuId = StringProperty()
    ProductASchema = StringProperty()
    ProductBSchema = StringProperty()
    ProductFamily = StringProperty()
    ProductId = StringProperty()
    ProductKind = StringProperty()
    ProductType = StringProperty()
    Properties = DictProperty(Property)
    SandboxId = StringProperty()
    SchemaVersion = StringProperty()
    ValidationData = DictProperty(ValidationData)


class MarketplaceCatalog(JsonObject):
    Aggregations = ListProperty(str)
    HasMorePages = BooleanProperty()
    ProductIds = ListProperty(str)
    Products = ListProperty(Product)
    TotalResultCount = IntegerProperty()


class PackageJson(object):
    def __init__(self, package):
        self._dict = package

    def get_packageformat(self):
        return self._dict.get('PackageFormat')

    # version (str)
    def get_version(self):
        return self._dict.get('Version', 0)

    def get_size(self):
        return self._dict.get('MaxDownloadSizeInBytes', 0)

    def get_download_urls(self):
        urls = self._dict.get('PackageDownloadUris', [])
        if not urls:
            return []
        return [uri['Uri'] for uri in urls]

    # contentId
    def get_content_id(self):
        return self._dict.get('ContentId', 'Unknown').upper()

    def __str__(self):
        return "Version: %s, Size: %i, ContentId: %s" % (
            self.get_version(), self.get_size(), self.get_content_id()
        )


class ProductJson(object):

    def __init__(self, product):
        self._dict = product

    # type
    def get_type(self):
        return self._dict.get('ProductType').lower()

    # oneStoreProductId
    def get_onestore_id(self):
        return self._dict.get('ProductId')

    # packageFamilyName
    def get_package_family_name(self):
        return self._dict.get('Properties', {}).get('PackageFamilyName', "")

    # name
    def get_name(self):
        return self._dict.get('LocalizedProperties', [{}])[0].get('ShortTitle')

    # productId
    def get_product_id(self):
        for prod_id in self._dict.get('AlternateIds', {}):
            if prod_id.get('IdType') == 'LegacyXboxProductId':
                return prod_id.get('Value')
        return ""

    def get_packages(self):
        ret = list()
        for sku in self._dict.get('DisplaySkuAvailabilities', {}):
            for package in sku['Sku'].get('Properties', {}).get('Packages', []):
                ret.append(PackageJson(package))

        return ret

    def __str__(self):
        return "%s - %s - %s - %s - %s" % (self.get_name(), self.get_package_family_name(),
                                      self.get_product_id(), self.get_type(), self.get_onestore_id())


class CatalogJson(object):
    def __init__(self, obj):
        if isinstance(obj, str):
            self._dict = json.loads(obj)
        elif isinstance(obj, dict):
            self._dict = obj
        else:
            raise Exception('Invalid data type: %s' % type(obj))

    def get_products(self):
        return [ProductJson(prod) for prod in self._dict['Products']]


def main():
    if len(sys.argv) < 2:
        print('Pass path to metadata json file')
        sys.exit(1)

    with io.open(sys.argv[1], 'rt') as f:
        data = json.load(f)

    catalog = CatalogJson(data)
    products = catalog.get_products()
    for idx, product in enumerate(products):
        print('%i) %s' % (idx, product))

    choice = int(input('Choose a title: '))
    product = products[choice]
    print('You chose: %s' % product)

    packages = product.get_packages()
    for idx, package in enumerate(packages):
        print('%i) %s' % (idx, package))

    choice = int(input('Choose a package: '))
    package = packages[choice]

    print('Download URL: %s' % package.get_download_urls())


if __name__ == "__main__":
    main()
