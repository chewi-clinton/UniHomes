UNI HOMES: A university housing solution application
Executive Summary.
Uni Homes is a mobile and web-based application which will solve the problem most university students in ICT University,Cameroon and Africa in general face in locating houses beside their university.Uni Homes offers so many unique and innovative features like
-allowing homes to be viewed in both 2D and 3D-interactive models
-save a home
-book a tour
-reserve a home
-comment under a home(review a home).
-In app map to see distance from the house to their school.

with a custom built distributed storage to ensure reliability(fault tolerance),scalability and supports global collaboration.By fixing errors or hurdles in housing search process,Uni homes main objective is to reduce time,reduce cost, reduce insecurity, provide houses that are students standard and providing transparency in finding university students accommodation .

The main vision of this project is to make an application which creates seamless,trust worthy and a technological advance solution to housing problems and also to provide transparency with virtual tours and a secure reservation process.

The initial target for this project is THE ICT UNIVERSITY. Which is located in Yaounde,Cameroon and with plans to scale to other schools in Cameroon and Africa.

Problem Description.
The major challenges linked to finding student home in Africa and Cameroon is
1)Limited universities with a dorm:Unlike most universities in the western world which offers dormitory or in campus housing Africa,Cameroon has very limited universities that offer dormitory or in campus housing and the initial target of this project ICT UNIVERSITY doesn’t offer this service So with the rapidly increasing rate of admissions of new students into the university and limited accommodations students often leave very far from school which has a great impact in their studies because most students miss classes or part of classes because they arrived school late,will be tired in class due to long journey before arriving schools etc.

2)Financial impact: The transportation cost when finding homes increases significantly because of repeated property visits.Also,most house owners(landlords,landladies) turn to increase their prices drastically because of house near school and Africa and Cameroon poor price regulatory policies. Again,the initial target ICT UNIVERSITY is a huge international recognized school so students leave from all regions to come school here and will have to pay to leave in hotels until they can find a house not far from school considering the fact that they are new to the town will even make manual house hunting difficult.Lastly,the cost to pay local house agents is very expensive in student areas.

3)Limited information and limited visibility: Very limited application exist in Africa with house listing specifically for university students and the initial target for this project has none so this makes house hunting very difficult and for the few applications that exist they show house images in 2D models only which is often so inaccurate because the rooms look larger in picture based on the angle it was taken and this often leads to disappointment when students or guardians visit the house physically.

4)Insecurity(Trust and verification issues):With the insecurity level in Africa and Cameroon it is very important for students to leave in a secured and comfortable environment.Unlike other existing home listing platforms which allows any landlord or house owner to provide homes for listing Uni Homes does thorough house inspections and property authenticity before providing a house for listing since students have almost no reliable way to verify property authenticity. All these is done so as to eliminate trust and verification issues

5)Time consuming:The local means of house hunting requires extraordinary investment of your time due to the fact that you will have to move asking around for available houses.Also, house agents often take students to
see multiple houses before they can make a choice which is very time consuming.

Problem Scope.  
The problem students face when seeking for houses around their universities in Africa and Cameroon is beyond mere availability,it includes many different areas which define the scope of their problem which Uni Homes solve.It includes several factors such as Geographical scope,Demographic Scope Financial boundary,Limited information ;

- Limited Information: There is no or limited platforms in Africa and Cameroon and initial target The ICT UNIVERSITY which is dedicated in serving African university student with housing option based on their school which makes house hunting difficult to get for new comers or new individuals in a university neighborhood to get suitable student houses.

- Financial scope : Most house listing platforms or house agent in Africa never go for student friendly priced homes even in urban areas, also these platform always lack a clear breakdown of all fees,utilities and often come with additional fees

- Geographical scope: Uni Homes is geographically focusing on African and Cameroon specific university areas with their initial target ICT UNIVERSITY in Yaounde so the target is specifically the neighborhood within 5km radius of the ICT UNIVERSITY campus .

- Demographic Scope: Uni Homes is here for everyone looking to relocate beside or in to a university neighborhood in Africa.
  a)Primary users: All university students both new and old and with our initial target being ICT UNIVERSITY we target students enrolled in the university.
  b) Secondary users:University staff and faculty responsible for student house management or student affairs.
  So they key factors affecting the problem is ;
  _ Affordability :differences in rental cost vs student budget
  _ Availability : The number of suitable available student homes vs demand
  _ Accessibility : Distance from school,safety,transportation infrastructure
  _ Transparency : Accurate,verifiable and trustworthy information about the listed homes \* User experience : Ease of search,reservation,booking and visualizing rooms and houses as they are physically .  
  Solution Proposal
  To mitigate or solve the issue mentioned above we are going to use an approach that combines a mobile application development using a client-server architecture together with a custom built distributed system storage. This approach will enhance efficiency, scalability and global collaboration in the house listing services and management. The solution here will be broken down into two parts General solution and distributed system storage solution.
  N.B. These two are one solution just broken down into two so I can make the explanation easier and clear to understand.

General solution: This section contains the general and innovative solution brought up to mitigate the earlier mentioned problems faced by university students and Africa.

- Core Solution components.
  - Mobile application : A mobile application was chosen for a complete intuitive user interface to enhance user experience and performance,accessibility when browsing,or reserving a house.A mobile platform chosed is a cross platform application to work on both iOS and android addressing the diverse device landscape among university students.Also a mobile app is efficient for loading and rendering media assets particularly the 3D model which require much resources when processing.
  - Property visualization : First there are two available media types to view a home which are in 2D and 3D images. The 2D images will have images of the home from different angles(exterior,rooms,toilet etc.) with image carousel and thumbnail navigation available while the 3D interactive model allow users to have a 360 degree view of the house.
  - Interactive Map View: An interactive map is available which shows distance from school to house and also the surrounding of the home so users can view without having to waste transportation going to the physical location before being able to check all of these things.
  - Rating by other students: Other students who have recently visited or leave in a home will be able to drop their honest review to let other students know if a house is good or not or if it matches it’s description in the listings
  - House reservation: A reservation fee will be paid and when approved the house will be removed from the listing for a period of 7 days and this house won’t be visible to anyone other than the user who paid for the reservation fee for this period and this will solve the issue of students in other location, towns regions or country who aren’t currently in the school neighborhood as in the case of our initial target THE ICT UNIVERSITY is Yaounde,Cameroon to be able to reserve a home they like so no other student has access to it.
  - Book tour :A booking fee will be paid and upon approval a house will be marked as booked for a period of 2 days in this period other users can still see the home in their listings that can add it to their saved homes to check it out in the future and during this period no other user can reserve this home. This will send a direct notification to the admin so he contact the student and go and show the house to the student. This is for students who are in the neighborhood of the university.
  - Payment Integration: Integration of the momo payment api provide seamless, transparent and secure payment which addresses all in app billing.
- Custom distributed storage system(Distributed system solution)
  _ This custom built distributed system represents a significant technological innovation in solving the student housing issues and this distributed file storage system will offer full control.
  _ The core goal of this distributed system is to create a fault tolerant storage system that allows - Uploading of 2D images and 3D models(.glb) through an API - Automatic replication of files across multiple storage nodes for reliability - Efficient serving of files through urls - Full control of the storage, replication and fault recovery
  How this will function;

1. File upload(2Dimages and 3D models). The files will be stored in one storage node and replicated to two other healthy node then the backend saved the metadata to a PostgreSQL database which will also have a master- slave replication relationship with another PostgreSQL database
2. Each file will be accessible through a unique url
3. Distributed storage node will support multiple nodes/servers
   High level benefit of this custom distributed storage system

- Scalability : I can add storage nodes when capacity demand increases
- Fault tolerance: File replication to several nodes ensures availability even if the primary node is shutdown or damaged
