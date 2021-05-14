from typing import List, Optional
import sys
import io
import json
import datetime 
from pydantic import BaseModel


class _Image(BaseModel):
    BackgroundColor: str
    Caption: str
    FileSizeInBytes: int
    ForegroundColor: str
    Height: int
    ImagePositionInfo: str
    ImagePurpose: str
    UnscaledImageSHA256Hash: str
    Uri: str
    Width: int


class _SearchTitle(BaseModel):
    SearchTitleString: str
    SearchTitleType: str


class PreviewImage(BaseModel):
    # BackgroundColor: None
    Caption: str
    FileSizeInBytes: int
    # ForegroundColor: None
    Height: int
    # ImagePositionInfo: None
    ImagePurpose: str
    UnscaledImageSHA256Hash: str
    Uri: str
    Width: int


class _Video(BaseModel):
    AudioEncoding: str
    Caption: str
    FileSizeInBytes: int
    Height: int
    PreviewImage: PreviewImage
    SortOrder: int
    Uri: str
    VideoEncoding: str
    VideoPositionInfo: str
    VideoPurpose: str
    Width: int


class _ContentRating(BaseModel):
    InteractiveElements: List[str]
    RatingDescriptors: List[str]
    RatingDisclaimer: List[str]
    RatingId: str
    RatingSystem: str


class _UsageData(BaseModel):
    AggregateTimeSpan: str
    AverageRating: float
    PlayCount: float
    PurchaseCount: float
    RatingCount: int
    RentalCount: float
    TrialCount: float


class ValidationData(BaseModel):
    PassedValidation: bool
    RevisionId: str
    ValidationResultUri: str


class _AlternateId(BaseModel):
    IdType: str
    Value: str


class _Attribute(BaseModel):
    # ApplicablePlatforms: None
    # Group: None
    Maximum: int
    Minimum: int
    Name: str


class _AllowedPlatform(BaseModel):
    MaxVersion: int
    MinVersion: int
    PlatformName: str


class ClientCondition(BaseModel):
    AllowedPlatforms: List[_AllowedPlatform]


class Condition(BaseModel):
    ClientConditions: ClientCondition
    EndDate: str
    ResourceSetIds: List[str]
    StartDate: str


class FulfillmentData(BaseModel):
    # Content: None
    PackageFamilyName: str
    ProductId: str
    SkuId: str
    WuBundleId: str
    WuCategoryId: str


class HardwareProperty(BaseModel):
    MinimumGraphics: str
    MinimumHardware: List[str]
    MinimumProcessor: str
    RecommendedGraphics: str
    RecommendedHardware: List[str]
    RecommendedProcessor: str

class _Application(BaseModel):
    ApplicationId: str
    DeclarationOrder: int
    Extensions: List[str]


class _FrameworkDependency(BaseModel):
    MaxTested: int
    MinVersion: int
    PackageIdentity: str


class _PlatformDependency(BaseModel):
    MaxTested: int
    MinVersion: int
    PlatformName: str


class _Package(BaseModel):
    Applications: List[_Application]
    Architectures: List[str]
    Capabilities: List[str]
    ContentId: Optional[str]
    DeviceCapabilities: List[str]
    DriverDependencies: List[str]
    ExperienceIds: List[str]
    FrameworkDependencies: List[_FrameworkDependency]
    FulfillmentData: FulfillmentData
    HardwareDependencies: List[str]
    HardwareRequirements: List[str]
    Hash: str
    HashAlgorithm: str
    IsStreamingApp: bool
    KeyId: str
    Languages: List[str]
    # MainPackageFamilyNameForDlc: None
    MaxDownloadSizeInBytes: Optional[int]
    MaxInstallSizeInBytes: int
    # PackageDownloadUris: None
    PackageFamilyName: str
    PackageFormat: str
    PackageFullName: str
    PackageId: str
    PackageRank: int
    PackageUri: str
    PlatformDependencies: List[_PlatformDependency]
    PlatformDependencyXmlBlob: str
    ResourceId: str
    Version: Optional[str]

    def get_packageformat(self):
        return self.PackageFormat

    # version (str)
    def get_version(self):
        return self.Version or 0

    def get_size(self):
        return self.MaxDownloadSizeInBytes or 0

    def get_download_urls(self):
        urls = self.PackageDownloadUris
        if not urls:
            return []
        return [uri.Uri for uri in urls]

    # contentId
    def get_content_id(self):
        return (self.ContentId or 'Unknown').upper()

    def __str__(self):
        return "Version: %s, Size: %i, ContentId: %s" % (
            self.get_version(), self.get_size(), self.get_content_id()
        )


class _Affirmation(BaseModel):
    AffirmationId: str
    AffirmationProductId: str
    Description: str


class _Remediation(BaseModel):
    Description: str
    RemediationId: str


class EligibilityProperty(BaseModel):
    Affirmations: List[_Affirmation]
    Remediations: List[_Remediation]


class PIFilter(BaseModel):
    ExclusionProperties: List[str]
    InclusionProperties: List[str]


class Price(BaseModel):
    CurrencyCode: str
    IsPIRequired: bool
    ListPrice: float
    MSRP: float
    TaxType: str
    WholesaleCurrencyCode: str
    WholesalePrice: float


class OrderManagementData(BaseModel):
    GrantedEntitlementKeys: List[str]
    PIFilter: PIFilter
    Price: Price


class Property(BaseModel):
    Attributes: List[_Attribute]
    CanInstallToSDCard: bool
    Categories: List[str]
    Category: str
    HasAddOns: bool
    IsAccessible: bool
    IsDemo: bool
    IsLineOfBusinessApp: bool
    IsPublishedToLegacyWindowsPhoneStore: bool
    IsPublishedToLegacyWindowsStore: bool
    # OwnershipType: None
    PackageFamilyName: str
    PackageIdentityName: str
    PdpBackgroundColor: str
    ProductGroupId: str
    ProductGroupName: str
    PublisherCertificateName: str
    PublisherId: str
    RevisionId: str
    # SkuDisplayGroups: None
    # Subcategory: None
    XboxLiveTier: str
    AdditionalIdentifiers: List[str]
    BundledSkus: List[str]
    # DisplayPhysicalStoreInventory: None
    # EarlyAdopterEnrollmentUrl: None
    FulfillmentData: FulfillmentData
    # FulfillmentType: None
    HardwareProperties: HardwareProperty
    HardwareRequirements: List[str]
    HardwareWarningList: List[str]
    HasThirdPartyIAPs: bool
    InstallationTerms: str
    IsBundle: bool
    IsPreOrder: bool
    IsRepurchasable: bool
    IsTrial: bool
    LastUpdateDate: str
    Packages: List[_Package]
    # SkuDisplayGroupIds: None
    SkuDisplayRank: int
    VersionString: str
    VisibleToB2BServiceIds: List[str]
    XboxXPA: bool
    OriginalReleaseDate: str


class _Availability(BaseModel):
    Actions: List[str]
    AlternateIds: List[_AlternateId]
    AvailabilityASchema: str
    AvailabilityBSchema: str
    AvailabilityId: str
    Conditions: Condition
    DisplayRank: int
    LastModifiedDate: str
    Markets: List[str]
    OrderManagementData: OrderManagementData
    Properties: Property
    RemediationRequired: bool
    SkuId: str


class LegalText(BaseModel):
    AdditionalLicenseTerms: str
    Copyright: str
    CopyrightUri: str
    PrivacyPolicy: str
    PrivacyPolicyUri: str
    Tou: str
    TouUri: str


class _LocalizedProperty(BaseModel):
    DeveloperName: str
    EligibilityProperties: EligibilityProperty
    Franchises: List[str]
    Images: List[_Image]
    Language: str
    Markets: List[str]
    ProductDescription: str
    ProductDisplayRanks: List[str]
    ProductTitle: str
    PublisherName: str
    PublisherWebsiteUri: str
    # RenderGroupDetails: None
    SearchTitles: List[_SearchTitle]
    ShortDescription: str
    ShortTitle: str
    SortTitle: str
    SupportUri: str
    Videos: List[_Video]
    VoiceTitle: str
    Contributors: List[str]
    # DeliveryDateOverlay: None
    # DisplayPlatformProperties: None
    Features: List[str]
    LegalText: LegalText
    MinimumNotes: str
    RecommendedNotes: str
    ReleaseNotes: str
    SkuButtonTitle: str
    SkuDescription: str
    SkuDisplayRank: List[str]
    SkuTitle: str
    # TextResources: None


class RelatedProduct(BaseModel):
    RelationshipType: str
    RelatedProductId: str


class _MarketProperty(BaseModel):
    # BundleConfig: None
    ContentRatings: List[_ContentRating]
    Markets: List[str]
    MinimumUserAge: int
    OriginalReleaseDate: datetime.datetime
    RelatedProducts: List[RelatedProduct]
    UsageData: List[_UsageData]
    # FirstAvailableDate: None
    # PackageIds: None
    SupportedLanguages: List[str]


class Sku(BaseModel):
    LastModifiedDate: str
    LocalizedProperties: List[_LocalizedProperty]
    MarketProperties: List[_MarketProperty]
    ProductId: str
    Properties: Property
    # RecurrencePolicy: None
    SkuASchema: str
    SkuBSchema: str
    SkuId: str
    SkuType: str
    # SubscriptionPolicyId: None


class _DisplaySkuAvailability(BaseModel):
    Availabilities: List[_Availability]
    Sku: Sku


class Product(BaseModel):
    AlternateIds: List[_AlternateId]
    DisplaySkuAvailabilities: List[_DisplaySkuAvailability]
    DomainDataVersion: str
    IngestionSource: str
    IsMicrosoftProduct: bool
    IsSandboxedProduct: bool
    LastModifiedDate: datetime.datetime
    LocalizedProperties: List[_LocalizedProperty]
    MarketProperties: List[_MarketProperty]
    MerchandizingTags: List[str]
    PartD: str
    PreferredSkuId: str
    ProductASchema: str
    ProductBSchema: str
    ProductFamily: str
    ProductId: str
    ProductKind: str
    ProductType: str
    Properties: Property
    SandboxId: str
    SchemaVersion: str
    ValidationData: ValidationData

    # type
    def get_type(self) -> str:
        return self.ProductType.lower()

    # oneStoreProductId
    def get_onestore_id(self) -> str:
        return self.ProductId

    # packageFamilyName
    def get_package_family_name(self) -> str:
        return self.Properties.PackageFamilyName

    # name
    def get_name(self) -> str:
        return self._dict.LocalizedProperties[0].ShortTitle

    # productId
    def get_product_id(self) -> Optional[str]:
        for prod_id in self.AlternateIds:
            if prod_id.IdType == 'LegacyXboxProductId':
                return prod_id.Value
        return ""

    def get_packages(self) -> List[_Package]:
        ret: List[_Package] = list()
        for sku in self.DisplaySkuAvailabilities:
            for package in sku.Sku.Properties.Packages:
                ret.extend(package)

        return ret

    def __str__(self) -> str:
        return "%s - %s - %s - %s - %s" % (self.get_name(), self.get_package_family_name(),
                                      self.get_product_id(), self.get_type(), self.get_onestore_id())


class MarketplaceCatalog(BaseModel):
    Aggregations: List[str]
    HasMorePages: bool
    ProductIds: List[str]
    Products: List[Product]
    TotalResultCount: int


def main():
    if len(sys.argv) < 2:
        print('Pass path to metadata json file')
        sys.exit(1)

    with io.open(sys.argv[1], 'rt') as f:
        data = json.load(f)

    catalog = MarketplaceCatalog(**data)
    for idx, product in enumerate(catalog.Products):
        print('%i) %s' % (idx, product))

    choice = int(input('Choose a title: '))
    product = catalog.Products[choice]
    print('You chose: %s' % product)

    packages = product.get_packages()
    for idx, package in enumerate(packages):
        print('%i) %s' % (idx, package))

    choice = int(input('Choose a package: '))
    package = packages[choice]

    print('Download URL: %s' % package.get_download_urls())


if __name__ == "__main__":
    main()
