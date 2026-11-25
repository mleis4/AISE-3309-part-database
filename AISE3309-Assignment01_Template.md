### Electrical and Computer Engineering

# AISE 3309: Database Management Systems

## Assignment 01

#### Requirement Specifications Document

|Group #:|6|
|---|---|
|Project Name:|Engineering Part Sourcer|
|Team Member Name|Team Member ID|
|1. Shaan Wrench|251422184|
|2. Mats Leis|251409940|
|3. Ayman Hossain|251430600|
|4. Samuel Huang|251418742|
|5. Anish Jami|251419182|

|1. 2. 3. 4.|3.1. 3.2.|||Table of Contents Project Overview....................................................................................................................................1 Functional Specifications........................................................................................................................1 Data Requirements ................................................................................................................................2 Entity Types:..................................................................................................................................2 Relationship Types.........................................................................................................................3 Contribution Specification......................................................................................................................4|
|---|---|---|---|---|
|1.||Project Overview Software Name Software Description|2. Functional Specifications (at least 6) Functionality Name|Engineering Part Sourcer Engineering Part Sourcer will help engineers find and compare parts from multiple distributors through a web application. Users will be able to search and filter components, compare prices and availability, and create or upload bills of materials to estimate project costs. Accounts will allow users to save BOMs and selected parts, while AI-assisted search will help translate component requirements into catalogue filters. The goal is to reduce manual sourcing work, organize supplier information, and support informed purchasing decisions. Functionality Description|
||Part Search|||Allows users to search for specific parts that they need by name, manufacturer part number, or keywords. The results will display matching parts and their specifications from the available suppliers listings across various sources.|
||Price Match|||Users can compare listings for a part across distributors. For example, requesting 10 units displays each supplier’s unit price, available stock, estimated shipping time, and subtotal, with offers sorted by price.|
||BOM upload|||Users can upload a CSV containing part numbers and required quantities. The system matches entries to catalogue parts, flags unmatched parts or invalid quantities.|

|Sign in|Users can register and sign in to save their BOMs and shopping cart. Returning users can reopen, edit, or delete their saved information.|
|---|---|
|Cart|Users can add supplier listings, adjust quantities, and remove items. The cart calculates item costs and groups subtotals by distributor. Users can follow links to the relevant supplier websites to purchase selected parts|
|Filter|Users can narrow results by category, dimensions, distributor, price range, and minimum stock. Results show matching parts and qualifying listings, with sorting by price or estimated shipping time.|
|BOM maker|Users can create a named BOM, add parts and quantities, and select supplier listings. The system calculates each line’s cost and the total parts cost, with shipping and taxes seperatly. It also flags quantities exceeding the selected supplier’s stock.|
|Project Sharing Upload|When users create/design projects using parts from our site, they will have the option to share those projects with other users by uploading their final designs and the parts they used on a separate page. This will be uploaded by Title, Description, and a list of all the parts used. People can look for these projects and order parts to replicate them if needed for their projects. These can also be portfolio pieces for users. This way you can get ideas from other users, replicate projects you need, and know the parts you are getting are correct and not from a third party website.|

# 3. Data Requirements

## <u>3.1. Entity Types (at least 4):</u>

|Entity Type Name|Client/Customer|
|---|---|
|Entity Type Description|A person who creates an account on the website. Signing in lets them search for parts, compare prices, save bills of materials, and keep a shopping cart between visits. Each customer is identified by their email address.|
|Attribute Name|Attribute Type|
|Name|Composite|
|FirstName|Simple|
|LastName|Simple|
|Username|Simple {CK}|
|Password|Simple|
|Email|Simple {PK}|
|Billing address|Composite (House/apt address, postal code, Unit number, city, province/state, country)|
|House/apt address|Simple|
|PostCode|Simple|
|UnitNum|Simple|
|City|Simple|
|Province|Simple|
|Country|Simple|

|Entity Type Name|Bill of materials||
|---|---|---|
|Entity Type Description||A named list of the parts and quantities needed for one project. A customer can build one on the website or upload an existing one. The website uses it to work out the total cost of the project.|
|Attribute Name||Attribute Type|
|BOM ID||Simple {PK}|
|BOM_name||Simple|
|Date_created||Simple|
|/Number of parts||Derived|
|/Total cost||Derived|

|Entity Type Name|Part|
|---|---|
|Entity Type Description|A specific component an engineer might need, such as a resistor, bolt, or connector. It stores the details that stay the same no matter who sells it, such as its manufacturer, category, material, and size. These details are what customers search and filter by.|
|Attribute Name|Attribute Type|
|Manufacturer_PartNum|Simple {PK}|
|Name|Simple|
|Description|Simple|
|Category|Simple|
|Distributor|Simple|
|Dimensions|Composite|
|Length|Simple|
|Width|Simple|
|Height|Simple|
|Datasheet_link|Simple|

|Entity Type Name|Distributor||
|---|---|---|
|Entity Type Description|where that distributor can deliver.|A company/retailor/seller that sells parts through the website, such as DigiKey, Mouser, McMaster-Carr, or LCSC. The website stores each distributor once and links it to every part it offers. Shipping regions record|
|Attribute Name||Attribute Type|
|DistributorID||Simple {PK}|
|Name||Simple {CK}|
|Website||Simple|
|Customer reviews||Multi-valued|
|/5-star rating||Simple|
|All parts||Multi-valued|

##### Entity Type Name Listing

|Entity Type Name|ShoppingCart|
|---|---|
|Entity Type Description|The listings a customer has chosen to buy, saved so they can check out all at once. Each customer has one cart. Its subtotal, shipping price, and total are calculated from the listings inside it.|
|Attribute Name|Attribute Type|
|Cart_ID|Simple {PK}|
|Date_Added|Simple|
|Parts|Multi-valued ([xxx,1],[yyy,3]....)|
|/Subtotal|Derived|
|/Shipping price|Simple|
|/Total price|Simple|

|Entity Type Description|possible.|One distributor's offer for one part. It stores the details that differ between sellers, such as price, stock, and lead time. A part sold by four distributors has four listings, which is what makes price comparison|
|---|---|---|
|Attribute Name||Attribute Type|
|Listing_ID||Simple {PK}|
|Distributor_PartNum||Simple|
|UnitPrice||Simple|
|Quantity||Simple|
|/EstShipTime||Simple|
|/LastUpdated||Simple|

## <u>3.2. Relationship Types</u>

|Relationship Type Name|DISTRIBUTOR Publishes LISTING|
|---|---|
|Relationship Description|A distributor puts up a listing to offer a part for sale at its own price and stock level.|
|Relationship Degree|2|
|Participating Entity Types|Distributor and listing|
|Attributes of Relationship|None|
|Participation|Distributor(1)-Listing(0,*)|
|Cardinality & Constraints|One-to-many. A distributor can publish many listings or none yet. Every listing must belong to exactly one distributor.|
|Relationship Type Name|LISTING Has PART|
|Relationship Description|Each listing is an offer for one specific part. This is what ties a seller's price and stock to the part being sold.|
|Relationship Degree|2|
|Participating Entity Types|Listing and part|
|Attributes of Relationship|None|
|Participation|Listing(0,*) - Part(1)|
|Cardinality & Constraints|Many-to-one. Every listing must be for exactly one part. A part can have many listings, or none if no distributor currently sells it.|
|Relationship Type Name|PART Alternative To PART|
|Relationship Description|Records that one part can be used in place of another, such as the same resistor made by two manufacturers. This lets the website compare prices across equivalent parts.|
|Relationship Degree|1|
|Participating Entity Types|Part|
|Attributes of Relationship|None|
|Participation|Part(0,*) - Part(0,*)|
|Cardinality & Constraints|Many-to-many. A part can have many substitutes or none.|

|Relationship Type Name|BOM Contains PART|
|---|---|
|Relationship Description|Records which parts are in a bill of materials and how many of each the project needs.|
|Relationship Degree|2|
|Participating Entity Types|BOM & Part|
|Attributes of Relationship|Quantity|
|Participation|BOM(0,*) - PART(0,*)|
|Cardinality & Constraints|Many-to-many. A BOM can contain many parts, and the same part can appear in many BOMs. Both sides are optional: a new BOM starts empty, and a part does not have to be in any BOM.|
|Relationship Type Name|Customer Creates BOM|
|Relationship Description|Entails how the user can create a BOM|
|Relationship Degree|2|
|Participating Entity Types|Part|
|Attributes of Relationship|List attributes if any (attribute 1, attribute 2, …)|
|Participation|Customer(1)-BOM(0,*)|
|Cardinality & Constraints|One-to-many. A customer can have many BOMs or none. Every BOM must belong to exactly one customer.|
|Relationship Type Name|Customer Owns ShoppingCart|
|Relationship Description|A customer has their own shopping cart connected to their specific account that saves their added items and allows them to order them all at once|
|Relationship Degree|2|
|Participating Entity Types|Customer & ShoppingCart|
|Attributes of Relationship|None|
|Participation|Customer(1) & ShoppingCart(1)|
|Cardinality & Constraints|One-to-one. A customer has at most one cart. Every cart must belong to exactly one customer.|

|Relationship Type Name|Customer Reviews Distributor|
|---|---|
|Relationship Description|Customers can leave a review on a distributor after purchasing a product from them|
|Relationship Degree|2|
|Participating Entity Types|Customer & Distributor|
|Attributes of Relationship|Customer Reviews, 5-star rating|
|Participation|Customer(0,* ) - Distributor (1,*)|
|Cardinality & Constraints|Many-to-many. A customer can review many distributors, and a distributor can be reviewed by many customers. Both sides are optional: a customer does not have to leave any reviews, and a new distributor has none yet.|

|Relationship Type Name|ShoppingCart Holds Listing|
|---|---|
|Relationship Description|Records which listings a customer has added to their cart and how many of each they want to buy. It links to listings, not parts, because the customer is choosing a specific distributor's offer.|
|Relationship Degree|2|
|Participating Entity Types|ShoppingCart & Listing|
|Attributes of Relationship|Quantity|
|Participation|ShoppingCart(0,*)-Listing(0,*)|
|Cardinality & Constraints|Many-to-many. A cart can hold many listings, and the same listing can be in many customers' carts. Both sides are optional: a cart can be empty, and a listing does not have to be in any cart.|

# 4. Contribution Specification

|Team Member Name: Anish Jami||
|---|---|
|Task/Contribution|Task Description|
|Functional Specifications|Added detail and more ideas on top of what Shaan and Mats worked on. Made the functions clearer and easier to understand, as well as ensuring that they fit within our project scope.|
|Project Overview and Review|Reviewed the document and created notes/fixed about mismatches with product functions and overall product direction. Worked with all of the team to establish a clear product idea: about what parts to simplify, and what to remove/add.|

|Team Member Name: Samuel Huang||
|---|---|
|Task/Contribution|Task Description|
|3.1 Entity Types|Filled out and reviewed the content added in the tables in this section with Ayman.|
|3.2 Relationship Types|Filled out and reviewed the content added in the tables in this section with Ayman.|

|Team Member Name: Ayman Hossain||
|---|---|
|Task/Contribution|Task Description|
|3.1 Entity Types|Enlisted the essential entities and their respective attributes with Samuel.|
|3.2 Relationship Types|Enlisted the essential relationships between entities, including all their relevant information, with Samuel.|

|Team Member Name: Shaan Wrench||
|---|---|
|Task/Contribution|Task Description|
|Project Overview|Came up with a detailed and logical description for our project with Mats. Main focus on user experience.|
|2 Functional Specifications|Came up with detailed functions for our web application with Mats, thinking about how users will interact with our site, what will set our site apart, and what makes the experience better.|

##### Team Member Name: Mats Leis

##### Task/Contribution Task Description

|Project Overview|Came up with a detailed and logical description for our project with Shaan. Main focus on user experience.|
|---|---|
|2 Functional Specifications|Came up with detailed functions for our web application with Shaan, thinking about how users will interact with our site, what will set our site apart, and what makes the experience better.|