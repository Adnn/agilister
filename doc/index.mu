= What is Agilister
Agilister is a user application to automatize the process of filling web forms, also handling the navigation in the websites for multiple-pages forms. Originally developed to post ads on specialized websites, it should apply equally well for automatizing the "user input" process for any website.

== Some example scenarios
* Posting a list of ads on several websites
* Automatizing an (increasing) list of regression tests on an evolving web UI
* Browsing bot for data mining
* Ranking up on dating websites  ; )
* etc.

= How does it work
Agilister is decoupling the actual entry's data the user would like to input on a web form, from metadata describing the structure of the forms on the website. It then uses Selenium to fire up a browser, and insert the values for the entry in the appropriate elements of the web forms, handling the submission(s) when necessary.
== The entries
An entry is responsible for providing the values necessary for completing an input form on a website.
//eg. In the scenario of posting ads, each ad is an entry.//
The actual data is a mapping of those values to keys (keys being generic names, shared by the different entries, that identify the values associated to them) : it could be a simple dictionary.
== Website metadata
The website metadata is given as a XML description file, and should be provided for each website. This description is based on the concept of actions :
//eg. On an auction website, you could want to :
*Log in
*Post a set of ads
*Browse for similar items and gather their listed price
Each of those items would map to one action.
//
For each action, an entry-point URL is provided : it is the first URL the browser will point to when the action is triggered. The action also has a list mapping each web element that will be filled to the key of the data that will be used as input for said element. 

= What does it buy me
So, in addition to writing down the data, Agilister requires its user to provide a description of the web form structure. Does not it only make the process heavier ?
Agilister needs a description of the structure of the website, but you only need to write it once. Even better, you can eventually use an existing description file. From here, you can automatically submit a list of entries on the website, as many times as you see fit.
Now, the biggest benefit is if you need to fill the same N entries on M websites. With a manual procedure, you would fill the all the entries once for each website, for a total of NxM interventions. With Agilister, you fill the N entries, and the M descriptions (if you do not already have them), requiring only N+M interventions in the worst case.

=Extensibility
Agilister was designed with modularity in mind. This is supported by an attempt at decoupling and clean interfaces.
The application ships with basic functionalities for reading entries data from XML files, and to input them to usual web form elements, applying a mapping statically written in the metadata.
But it mainly provides a framework to be extended, in order to :
*Obtain data from other sources (Databases, worksheets, programmatic generation, ...).
*Set the data to new elements (eventually added to the standard in the future), or fill existing elements with a different behavior.
*Handle any arbitrary mapping of data to web elements, even dynamic.
Achieving any of those points in isolation is a matter of subclassing a single class with well defined responsibilities, without messing with other parts of the system. But the possibilities are multiplied by doing several in conjonction. 
==Data sources
Decoupling entry data from website metadata gives the benefits of reusability. It also allows the entries data to be obtained from virtually any imaginable source, by writing a <code>DataFeeder</code> subclass handling the source and conforming to simple and minimal interface. No need to modify the other concepts, the interaction between classes are done through newcomer-friendly interfaces.


= Documentation entries
* [[API Reference]]
* [[Design decisions]]