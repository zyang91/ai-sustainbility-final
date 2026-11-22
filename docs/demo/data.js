// Recorded runs of the real pipeline (penn_rag). Answers are verbatim model output.
// Passages that the answer did not cite are shortened to about 320 characters.
window.DEMO = {
 "recorded": "22 Nov 2026",
 "model": "llama3.1:8b in Ollama",
 "years": [
  1948,
  1961,
  1963,
  1966,
  1977,
  1978,
  1979,
  1982,
  1983,
  1984,
  1987,
  1992,
  1998,
  2006,
  2012,
  2018
 ],
 "runs": [
  {
   "id": "parking-1961",
   "question": "How many off-street parking spaces did the 1961 plan project for 1965 and 1970?",
   "kind": "A figure from a table",
   "check": "ok",
   "note": "Both figures are in the Total row of Table IV on page 29 of the 1961 plan: 3,000 spaces for 1965 and 3,300 for 1970.",
   "steps": [
    {
     "query": "How many off-street parking spaces did the 1961 plan project for 1965 and 1970?",
     "compare": true,
     "year_from": 1961,
     "year_to": 1970
    }
   ],
   "answer": "According to the 1961 plan, the projected essential off-street parking requirements for 1965 and 1970 are:\n\n* 1965: 3,000 spaces [2]\n* 1970: 3,300 spaces [2]\n\nThese numbers are based on the TABLE \"Number of Spaces\" in the 1961 plan [2].",
   "cited": [
    2
   ],
   "sources": [
    {
     "n": 1,
     "short": "Development Plan",
     "year": 1961,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 28,
     "page_end": 28,
     "text": "Total Existing and Projected Essential Off-Street Parking Requirements of University Population and Visitors 1960-61, 1965, and 1970"
    },
    {
     "n": 2,
     "short": "Development Plan",
     "year": 1961,
     "status": "final",
     "kind": "table",
     "section": "",
     "page_start": 29,
     "page_end": 29,
     "text": "Number of Spaces\nFunctional Category 1960-61 1965 1970\nAdministration and University\nServices 135 130 185\nAthletics 40 40 35\nBiological and Medical Sciences 425 475 500\nFine Arts 50 80 75\nGraduate Studies 1 55\nHumanities 225 320 340\nLaw Library 55 30 110 90 75 85\nPhysical Sciencesaand Engineering 325 380 420\nServices and Activities 55 55 65\nSocial Sciences 365 530 720\nUniversity Hospital 610 700 620\nUniversity Museum 85 90 125\nTotal 2,400 3,000 3,300\nSource: A Proposed Off-Street Parking Plan, An Element\nof the U of P Development Plan."
    },
    {
     "n": 3,
     "short": "Development Plan",
     "year": 1963,
     "status": "final",
     "kind": "text",
     "section": "Entrances and Exits",
     "page_start": 31,
     "page_end": 31,
     "text": "The University has reviewed the complex of transportation facilities serving the Campus and the present transportation requirements of the faculty, students, administrative personnel, and visitors. The University desires to maintain a balanced system of transportation service to the Campus. Off street parking is one …"
    },
    {
     "n": 4,
     "short": "Development Plan",
     "year": 1963,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 18,
     "page_end": 18,
     "text": "Total Existing and Projected Essential Off-Street Parking Requirements of"
    },
    {
     "n": 5,
     "short": "Campus Development Plan",
     "year": 1966,
     "status": "final",
     "kind": "text",
     "section": "Transportation",
     "page_start": 30,
     "page_end": 30,
     "text": "The University has reviewed the complex of transportation facilities serving the Campus and the present transportation requirements of the faculty, students, administrative personnel, and visitors. The University desires to maintain a balanced system of transportation service to the Campus. Off-street parking is one …"
    },
    {
     "n": 6,
     "short": "Campus Development Plan",
     "year": 1966,
     "status": "final",
     "kind": "table",
     "section": "Parking",
     "page_start": 18,
     "page_end": 18,
     "text": "Number of Spaces\n1960-61 1970\nFull-Time Students 1 600 2,160\nUniversity Personnel 1,350 1,865\nVisitors to University 450 225\nTOTAL 2,400 4,250"
    }
   ]
  },
  {
   "id": "cars-1977",
   "question": "What did the 1977 Landscape Development Plan say about cars and parking lots on campus?",
   "kind": "One plan",
   "check": "ok",
   "note": "Every figure quoted is in the cited pages of the 1977 plan: the 3 to 1 legal margin, 4,132 spaces, 325 square feet per space and 30.8 acres.",
   "steps": [
    {
     "query": "cars and parking lots on campus",
     "compare": false,
     "year_from": 1977,
     "year_to": 1977
    }
   ],
   "answer": "The 1977 Landscape Development Plan stated that the University is well within the parking legal requirement, with a margin of 3 to 1, and that the campus surface parking lots are one of the highest revenue-generating operations per dollar invested (1977, [3]). However, the plan also noted that the existence of parking facilities generates parking demand that would not have otherwise existed, and that environmental and aesthetic considerations argue against an access program that encourages automobile usage (1977, [3]).\n\nThe plan also mentioned that there are 4,132 campus off-street parking spaces, consuming an average of 325 square feet for stalls and aisles, and that the total off-street campus area consecrated to the automobile is 30.8 acres (1977, [4]).\n\nAdditionally, the plan noted that service vehicles were forced to use nearly every major pedestrian path due to the many new buildings and street closings of the 1960s, but that recent policy to limit heavy service vehicles to cul-de-sacs off of city streets has been relatively successful in promoting more efficient servicing and reducing possible vehicular-pedestrian conflicts (1977, [5]).\n\nOverall, the 1977 Landscape Development Plan highlighted the challenges and complexities of managing parking and vehicle traffic on campus, and emphasized the need for a critical evaluation of the role of the automobile in the campus access pattern.",
   "cited": [
    3,
    4,
    5
   ],
   "sources": [
    {
     "n": 1,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 41,
     "page_end": 42,
     "text": "Parking for private automobiles poses many difficult problems for an institution as large as the University. In terms of its amount, kind, and location, parking also tends to generate, concentrate, and congest traffic. The numerous parking lots within the campus and the large areas devoted to cars Campus access and …"
    },
    {
     "n": 2,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 43,
     "page_end": 43,
     "text": "Buildings without adequate space for compactors (such as the Graduate School of Fine Arts, Furness library, and Hayden Hall) dispose of their refuse in smaller interior and exterior storage areas. A more conspicuous aspect of campus refuse collection are the 120 red-topped trash cans, which have significantly reduced …"
    },
    {
     "n": 3,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 42,
     "page_end": 42,
     "text": "The University is so well within the parking legal requirement, by a margin of 3 to 1, that it does not represent a constraint in the University's overall access program for the foreseeable future. In spatial terms, the area needed for storing one car is equivalent to a classroom size for twenty students, or more than twice the area for an average-sized office. On the other hand, the campus surface parking lots are one of the highest revenue generating operations per dollar invested, and since they are so quickly amortized, are useful as temporary land-banking improvements. From the social perspective, the campus parking facilities and administration service the demand generated by the driving University and University visitor population. To some extent, however, the mere existence of these same parking facilities and their marketing through various mechanisms generates parking demand that would not have otherwise existed (by reason of the economic law of marginal utility). Environmental and aesthetic considerat ons argue against an access program which encourages automobile usage... In sum, since the automobile has assumed such major proportions in the present campus access pattern ... a critical evaluation of its role in the context of an overall campus access program needs to be one of the first priorities... Such an evaluation would be most meaningfully pursued if there were a concurrent exploration of other means for accommodating campus needs\" (op. cit. above, p. 1.3)."
    },
    {
     "n": 4,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 42,
     "page_end": 42,
     "text": "Although there have been several parking studies of the campus in recent years, a brief summary of the issues is contained in \"A Proposed Campus Access Program\": \"When one considers that there are 4,132 campus off-street parking spaces, each consuming on the average of 325 square feet for stalls and aisles, then the total off-street campus area consecrated to the automobile is 1,342,900 square feet, or 30.8 acres. This translates into a parking/building ratio of 1 to 4.3, in other words one square foot of campus offstreet parking area for every 4.3 square feet of campus gross building area (excluding garage areas). The Institutional Development District zoning requirement for campus offstreet parking is one car space per 4,000 square feet of gross building area, or a parking/building ratio of 1 to 12.3."
    },
    {
     "n": 5,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 43,
     "page_end": 43,
     "text": "To function efficiently, the campus requires a clear access system for refuse-collection, delivery, and maintenance vehicles. With the many new buildings and street closings of the l960s, service vehicles were forced to use nearly every major pedestrian path. Recent policy to limit heavy service vehicles (shown by thick lines) to cul-de-sacs off of city streets has been relatively successful in both promoting more efficient servicing and reducing possible vehicular-pedestrian conflicts. Refuse collection comprises the largest component of the campus service system, in terms of both the number and size of vehicles. An average of 89 tons of refuse is removed from the campus each week, primarily from dumpsters and compactors located near most major buildings. Trucks presently serve these compactors off city streets and do not enter the pedestrian zones, with the exception of the major trash-collection area for the men's quads on Hamilton Walk."
    },
    {
     "n": 6,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "SUMMARY OF INVENTORY FINDINGS",
     "page_start": 38,
     "page_end": 38,
     "text": "Although large sums of money have in recent years been spent on new buildings, the funding allotted to the landscape proper has proportionately decreased. This has led to a widespread use of materials with a low initial cost and short life span. Nowhere is this more evident than in the campus paths, curbs, and drains. …"
    }
   ]
  },
  {
   "id": "river-2006",
   "question": "What did Penn Connects (2006) propose for the land east of campus along the Schuylkill River?",
   "kind": "One plan",
   "check": "ok",
   "note": "Each item is in the cited pages of Penn Connects (2006). The garage at South Street is described there as a connection, not as a new proposal of this section.",
   "steps": [
    {
     "query": "Penn Connects proposal for land east of campus along Schuylkill River",
     "compare": false,
     "year_from": 2006,
     "year_to": 2006
    }
   ],
   "answer": "The Penn Connects Vision Plan proposes the following for the land east of campus along the Schuylkill River:\n\n* A new signature sports and recreation park east of Franklin Field on the site of the existing Bower Field and the surface parking areas of the postal lands [3].\n* A series of new public gathering and circulation spaces in the Palestra and Franklin Field area that serve to link the postal lands to the campus [3].\n* Significant development potential for future academic, research and supporting program elements [3].\n* Connections and future expansion potential between the River Fields area and the medical district [3].\n* A new pedestrian bridge over the Schuylkill River, extending Locust Walk through the revitalized athletics complex, continuing onto new fields, and culminating in a new pedestrian bridge over the Schuylkill River [4].\n* A universal performing art space, conference center, retail shopping and dining, daycare, research space, and non-academic offices relocated from the core of campus [5].\n* A new garage proposed at South Street [4].\n* A bicycle network that links with existing and proposed routes in the University City context and along the Schuylkill River corridor [6].\n* Improved service to the east campus area and medical district of the campus through University City Station [6].\n* Intersection improvements at University Avenue and River Fields Road, along South Street, at 33rd and Spruce, and in the 30th Street Station area [6].\n\nAll of these proposals are from the 2006 Penn Connects plan.",
   "cited": [
    3,
    4,
    5,
    6
   ],
   "sources": [
    {
     "n": 1,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 35,
     "page_end": 35,
     "text": "Penn Connects provides the University of Pennsylvania with a clear vision for the future – a vision responding to the history and tradition of the campus, the surrounding urban context, and the previous planning and urban design initiatives that have transformed the Penn campus: College Green, Locust, Woodland and …"
    },
    {
     "n": 2,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 59,
     "page_end": 61,
     "text": "Proposed crossing point of the Research Bridge over the rail lines and under the Highline in the area of University City Station Campus Vision Connecting the University to the City and the City to the University is central to the Penn Connects vision for the campus. The vision emerges from a broader goal of …"
    },
    {
     "n": 3,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 61,
     "page_end": 61,
     "text": "corridor. • \tEstablishes new connections and gateways between the campus, Center City and surrounding areas in West Philadelphia at the Walnut Street and South Street Bridges; • \tCreates a new signature sports and recreation park east of Franklin Field on the site of the existing Bower Field and the surface parking areas of the postal lands; • \tProvides for a series of new public gathering and circulation spaces in the Palestra and Franklin Field area that serve to link the postal lands to the campus; • \tAccommodates significant development potential for future academic, research and supporting program elements; and • \tCreates connections and future expansion potential between the River Fields area and the medical district; The Penn Connects Vision Plan is described in the following sections in terms of civic and open space structure, circulation linkages, land use and development zones. View of the east campus area with the surface parking area of the postal lands in the foreground. Vision for the east campus area as viewed from the Walnut Street Gateway."
    },
    {
     "n": 4,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 65,
     "page_end": 67,
     "text": "Bridges of Connectivity link the major infill development and mixed-use nodes of the campus. The reconstructed south street bridge will become the Health Science and Cultural Bridge. Schuylkill River Corridor. The landscape structure of the east campus is intended to link with the Schuylkill Banks Park system east of the river. The research bridge will connect the medical district, including the Center for Advanced Medicine (CAM), with the long-term expansion potential identified in the River Fields area. The Sports and Recreation Bridge serves as the extension of Locust Walk, connecting College Green with new open spaces at the Palestra and Franklin Field. It extends eastward, providing access to the sports and recreation fields and across the Schuylkill River to connect with the Schuylkill Banks Park system. • The Sports and Recreation Bridge – extends Locust Walk through the revitalized athletics complex, continuing onto new fields and culminating in a new pedestrian bridge over the Schuylkill River. It links with Franklin Field and the Palestra area, which are regenerated, and provides connection to a major garage proposed at South Street."
    },
    {
     "n": 5,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 41,
     "page_end": 43,
     "text": "• Cultural - universal performing art space • Conference center - hotel, international conferences, continuing • Retail shopping and dining • Daycare • Research - flexible interdisciplinary space, corporate co-location • Non-academic offices relocated from core of campus • Parking The planning process focused on evaluating the connectivity, adjacencies and other physical factors such as visibility, the Schuylkill River floodplain, and rail and roadway corridors that traverse the land, and how and where this probable list of program needs might be best accommodated. Framed by College Hall, the Van Pelt Library and the Fisher Fine Arts Library, College Green now serves as the key central open space of the campus. The closure of Locust, Woodland and 36th Streets represents an important planning strategy which today provides Penn with a very pleasant and comfortable pedestrian oriented campus. Collectively, these routes form the key spines of pedestrian movement and connectivity on the campus. As called for in the 2001 Campus Development Plan, the Vision Plan extends and enhances these key routes to integrate the east campus area, Hill Square and the Walnut Street corridor into the campus environment. Improvements made along Walnut Street over the last 20 years through infill development and direct investment by the University also represent noteworthy initiatives that link the campus with the surrounding urban context."
    },
    {
     "n": 6,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 91,
     "page_end": 91,
     "text": "The Plan extends the bicycle network of the campus to link with existing and proposed routes in the University City context and along the Schuylkill River corridor. As with the pedestrian network, these routes are coordinated with the transit services and major stations that serve the campus. Major extensions of the network are proposed in the east campus area with new routes along South Street, on the proposed Schuylkill River pedestrian bridge, and a north / south route along the Lower 31st Street extension. The Penn campus is well served by a number of University and SEPTA bus routes and regional and national rail services. Several bus routes run through the campus and several transit stations are located on the campus and in the surrounding context. Analysis of the stations reveals that a majority of the entire campus area is within a five to 10 minute walk of a transit station. University City Station, in particular, provides a major opportunity for improved service to the east campus area and medical district of the campus. Vehicular circulation recommendations focus on intersection improvements at University Avenue and River Fields Road, along South Street, at 33rd and Spruce and in the 30th Street Station area. This section summarizes the circulation and parking recommendations of the Vision Plan."
    }
   ]
  },
  {
   "id": "pedestrian",
   "question": "When did Penn begin emphasizing pedestrian environments and open space?",
   "kind": "Change over time",
   "check": "partial",
   "note": "The 1950s date is real but second-hand: it comes from the 1992 plan looking back, because the archive has no plan from the 1950s. The answer also leaves out the 1960s plans, which were retrieved.",
   "steps": [
    {
     "query": "When did Penn begin emphasizing pedestrian environments and open space?",
     "compare": true
    }
   ],
   "answer": "The plans mention that the University made a second defining decision in the 1950s to create a pedestrian core by closing Woodland Avenue and relocating its trolleys to a new subway-surface system [11]. This decision reinforced Penn's goal of becoming a residential University attractive to the very best undergraduates from across the country.\n\nThe plans also mention that the Landscape Architecture Master Plan (LAMP) and its centerpiece, the conversion of College Green to Blanche Levy Park, highlighted the importance of the campus' pedestrian core in the 1970s [12]. LAMP taught the University two important lessons: that good land-use planning involves principles and guidelines rather than a detailed drawing of a future that time and circumstance would likely deny; and that good land-use planning requires a vision of how the University as a whole fits together and of the central importance of shared space.\n\nThe plans also mention that the 1977 Landscape Development Plan (LDP) emphasized the importance of pedestrian environments and open space, and that the goal of the landscaping program should be to reinforce the images of the campus' individual places, making their physical and functional relationships and organizations more legible [14, 15].\n\nTherefore, it appears that Penn began emphasizing pedestrian environments and open space in the 1950s, with a major shift in the 1970s towards creating a more pedestrian-friendly campus through the LAMP and LDP.",
   "cited": [
    11,
    12,
    14,
    15
   ],
   "sources": [
    {
     "n": 1,
     "short": "Campus Development Plan",
     "year": 1966,
     "status": "final",
     "kind": "text",
     "section": "Schuylkill River Frontage",
     "page_start": 27,
     "page_end": 29,
     "text": "The Development Plan extends the present eastern boundary of the Campus, between Walnut and South Streets, eastward to the Schuylkill River. This area will be required for the expansion of the Physical Sciences Research area, the 1. The following document, completed for the University since the above was written, …"
    },
    {
     "n": 2,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 34,
     "page_end": 35,
     "text": "comparable in size with the open space network of the Society Hill and Independence Mall area, and with William Penn's five original Philadelphia city squares combined. Although the campus-city interface is extensive, comprehension of the campus as a special place occurs at critical points along the approach routes …"
    },
    {
     "n": 3,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 19,
     "page_end": 19,
     "text": "initiatives that would further enliven the campus environment. Notes to the text 1 Reprinted in Thomas Harrison Montgomery's A History of the University of Pennsylvania from its Foundation to AD 1770 (Philadelphia: George W. Jacobs & Co., 1900), p. 497. \"Minutes of the Special Committee on Endowment, 6 October l868\", …"
    },
    {
     "n": 4,
     "short": "Development Plan, Interim Report",
     "year": 1979,
     "status": "draft",
     "kind": "text",
     "section": "B.3 Open Space",
     "page_start": 39,
     "page_end": 39,
     "text": "The University Landscape Plan sets out many of the necessary ideas for the creating of quality open spaces at Pennsylvania. In the following discussion we focus only on open space issues that are directly linked to changes we propose to the University building fabric. The present order of open space on the campus may …"
    },
    {
     "n": 5,
     "short": "Development Plan, Interim Report",
     "year": 1979,
     "status": "draft",
     "kind": "text",
     "section": "L.A.2 OPEN SPACE",
     "page_start": 25,
     "page_end": 25,
     "text": "between 38th and 39th Streets and Walnut and Locust Streets, Hamilton Walk and Smith Walk. The buildings that flank these places generally conform to the vernacular pattern described above. The borders between the buildings and the open spaces are clearly set off; while not monumental they are determined. These …"
    },
    {
     "n": 6,
     "short": "Campus Development Plan Reports, 1981–82",
     "year": 1982,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 82,
     "page_end": 82,
     "text": "What is far more legible is the way streets define the edges of precincts within the overall campus. Here, the combination of edge/street continuity, the pedestrian-only super blocks and the more comprehensible size of these sub-areas make extensive use of the street as an edge. For example, the central Campus is …"
    },
    {
     "n": 7,
     "short": "Campus Development Plan Reports, 1982–83",
     "year": 1983,
     "status": "final",
     "kind": "text",
     "section": "F. PREVIOUS COMMERCIAL AND LAND-USE PATTERNS",
     "page_start": 45,
     "page_end": 45,
     "text": "A drastic change in the commercial service offerings in University City has taken place in the last thirty years. This change is principally due to actions taken by the University and the Philadelphia Redevelopment Authority during the early 1960's. Compare the maps in Figures 12 and 13. Prior to about l960 the area …"
    },
    {
     "n": 8,
     "short": "Campus Development Plan Reports, 1982–83",
     "year": 1983,
     "status": "final",
     "kind": "text",
     "section": "1.A LANGUAGE OF ENTRANCES ON CAMPUS",
     "page_start": 83,
     "page_end": 84,
     "text": "Entrances are the junctures between inside and outside; between the rooms and corridors of a building and the streets, walks and public open spaces of the Campus. On the Penn Campus, the connection between an outdoor public space and the interior spaces of the building are made in a great variety of ways. Some are as …"
    },
    {
     "n": 9,
     "short": "Campus Master Plan",
     "year": 1987,
     "status": "draft",
     "kind": "text",
     "section": "A Brief History of Campus Planning at Penn",
     "page_start": 53,
     "page_end": 53,
     "text": "Penn has a long tradition of campus planning. From the time of its move to West Philadelphia in 1879 until 1913, the campus grew without any formal development scheme. Buildings were sited in groups in accordance with the topography and the street grid. The result was a campus \"without organic arrangement,\" according …"
    },
    {
     "n": 10,
     "short": "Campus Master Plan",
     "year": 1987,
     "status": "draft",
     "kind": "text",
     "section": "Track One: Informational—The Planning Context",
     "page_start": 53,
     "page_end": 53,
     "text": "The Penn campus of today is strongly oriented along a series of east/ west axes. This major shift from the original north/south orientation emerged slowly as the natural outcome of growth along the major streets which extended west and southwest when the rapid expansion of the 1960's began. Numerous cross streets were …"
    },
    {
     "n": 11,
     "short": "Master Land Use Plan",
     "year": 1992,
     "status": "draft",
     "kind": "text",
     "section": "A. INTRODUCTION",
     "page_start": 6,
     "page_end": 6,
     "text": "Then, in the 1950s, the University made a second defining decision: to create within the campus a pedestrian core by closing Woodland Avenue and relocating its trolleys to a new subway-surface system. The closing of Woodland Avenue gave the campus a pedestrian core, thus reinforcing Penn's goal of becoming a residential University attractive to the very best undergraduates from across the country. In the decades that followed, new student residences were built to both the east and west of the campus, and Van Pelt-Dietrich Library came to define the northern boundary of College Green. The construction of the Annenberg Center brought the performing arts to the center of the campus. New homes were constructed for the Wharton School, the School of Social Work, the Graduate School of Education, the Graduate School of Fine Arts and the Annenberg School, and expanded facilities were constructed for the School of Law, the School of Engineering and Applied Science, and the School of Dental Medicine."
    },
    {
     "n": 12,
     "short": "Master Land Use Plan",
     "year": 1992,
     "status": "draft",
     "kind": "text",
     "section": "A. INTRODUCTION",
     "page_start": 6,
     "page_end": 6,
     "text": "In the 1970s, the importance of the campus' pedestrian core was highlighted by the development of the Landscape Architecture Master Plan (LAMP) and its centerpiece, the conversion of College Green to Blanche Levy Park. LAMP taught the University two important lessons: that good land-use planning involves principles and guidelines rather than a detailed drawing of a future that time and circumstance would likely deny; and that good land-use planning requires a vision of how the University as a whole fits together and of the central importance of shared space (Blanche Levy Park), people connectors (Locust Walk), the preservation of the campus' historical treasures (the Furness Building), and the integration of academic facilities (the Laboratory for Research on the Structure of Matter). Those lessons frame the land-use plan we now submit to the Board of Trustees of the University of Pennsylvania. The plan itself grew out of extensive discussions within the University over the last four years. It includes a sense of how the University's schools might best develop their facilities, the potential growth of Penn's on-campus housing, the development of a University retail zone, the expansion of the University's recreational precinct, and the extension of the University's pedestrian core, including an integrated set of walkways complementing Locust Walk."
    },
    {
     "n": 13,
     "short": "Campus Development Master Plan",
     "year": 1998,
     "status": "draft",
     "kind": "text",
     "section": "STREETS AND GATEWAY STRATEGIES",
     "page_start": 68,
     "page_end": 68,
     "text": "Campus streets are not well defined as part of Penn or as pedestrian spaces. Streets, street corners and major intersections offer opportunities to strengthen existing image of the campus. The image of the campus edge, whether perceived as a boundary or a zone of activity is very important to the sense of the campus …"
    },
    {
     "n": 14,
     "short": "Campus Development Master Plan",
     "year": 1998,
     "status": "draft",
     "kind": "text",
     "section": "LANDSCAPE STRATEGIES",
     "page_start": 74,
     "page_end": 74,
     "text": "The campus identity should be strenghthened by consistent use of design guidelines and principles identified in the Landscape Development Plan of 1977. The goal of the landscaping program should be to reinforce the images of the campus' individual places, making their physical and functional relationships and organizations more legible. As major developments extend beyond the core, it is increasingly more important to extend the campus fabric using what is identified in the Campus Landscape Development Plan as \"tartan grid\" concept - a weave of major and minor pedestrian links extended wherever they reach into the urban context using the campus landscape standards. The network of Pedestrian links should complement and reflect the interactive quality of the Penn Community. The Campus Development Master Plan should also review campus pedestrian corridors and gateways, focus on lack of Pedestrian amenities along major pedestrian corridors, extend landscape vocabulary beyond the campus core."
    },
    {
     "n": 15,
     "short": "Campus Development Plan, Executive Brief",
     "year": 1998,
     "status": "final",
     "kind": "text",
     "section": "Strategies",
     "page_start": 16,
     "page_end": 16,
     "text": "The campus identity should be strengthened by consistent use of design guidelines and principles identified in the Landscape Development Plan (LDP) of 1977. The goal of the landscaping program should be to reinforce the images of the campus' individual places, making their physical and functional relationships and organizations more legible. along major pedestrian corridors. Other major initiatives should concentrate on the streetscape and gateway approaches to campus; the dwindling health of canopy or shade trees over the entire campus; and urban greenways linking to other public green spaces near campus. As development extends beyond the core, it is increasingly important to plan the campus fabric using what is identified in the LDP as a \"tartan grid\" concept -- a weave of major and minor pedestrian links extended wherever they reach into the urban context using the campus landscape standards. The network of pedestrian links should complement and reflect the interactive quality of the Penn Community."
    },
    {
     "n": 16,
     "short": "Campus Development Plan, Executive Brief",
     "year": 1998,
     "status": "final",
     "kind": "text",
     "section": "Athletics And Recreation Strategies",
     "page_start": 28,
     "page_end": 30,
     "text": "2. Renovation of the Palestra into a multipleuse major recreation site and auditoria Local parks, including Hill Field on campus and Clark Park, offer space for play, strolling, and casually organized sports games. The Biological Garden and the Woodlands offer the opportunity to connect a greensward from campus to the …"
    },
    {
     "n": 17,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 41,
     "page_end": 43,
     "text": "• Cultural - universal performing art space • Conference center - hotel, international conferences, continuing • Retail shopping and dining • Daycare • Research - flexible interdisciplinary space, corporate co-location • Non-academic offices relocated from core of campus • Parking The planning process focused on …"
    },
    {
     "n": 18,
     "short": "Penn Connects",
     "year": 2006,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 59,
     "page_end": 61,
     "text": "Proposed crossing point of the Research Bridge over the rail lines and under the Highline in the area of University City Station Campus Vision Connecting the University to the City and the City to the University is central to the Penn Connects vision for the campus. The vision emerges from a broader goal of …"
    },
    {
     "n": 19,
     "short": "Penn Connects 2.0",
     "year": 2012,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 61,
     "page_end": 61,
     "text": "Penn Connects (2006) reinforces the well-established open space framework of the campus broadly defined by Locust Walk, Woodland Walk and College Green, and introduced a vision for Penn Park. With the completion of Penn Park, a key aspect of the proposed civic framework has now been realized. Penn Connects 2.0 …"
    },
    {
     "n": 20,
     "short": "Penn Connects 2.0",
     "year": 2012,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 25,
     "page_end": 27,
     "text": "EXISTING View of the New College House site Penn Connects 2.0 includes multiple open space projects that advance local engagement and ensure that Penn is more meaningfully connected to the surrounding community and improves the public realm of the campus and surrounding urban context. They will enhance the campus …"
    },
    {
     "n": 21,
     "short": "Penn Connects 3.0",
     "year": 2018,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 1,
     "page_end": 3,
     "text": "Penn Connects 3.0 includes multiple open space projects that improve the public realm of the campus and its surrounding urban context. These projects will enhance the campus experience for pedestrians and cyclists and physically improve connections to the City beyond. Streetscape plans will prioritize pedestrian …"
    },
    {
     "n": 22,
     "short": "Penn Connects 3.0",
     "year": 2018,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 5,
     "page_end": 5,
     "text": "REALIZING THE VISION Since the Penn Connects vision was outlined in 2006, the University has significantly been transformed as a unique, urban campus with strong connections to both the local community and global context. Penn Connects: A Vision for the Future established a major physical presence for the University …"
    }
   ]
  },
  {
   "id": "parking-change",
   "question": "How did Penn's parking policies evolve between the 1960s and 1970s?",
   "kind": "Change over time",
   "check": "bad",
   "note": "The first claim is wrong. Source 1 is about housing units for undergraduate men, not parking, and no passage says the University was \"laissez-faire\". The 1977 and 1979 quotations are accurate.",
   "steps": [
    {
     "query": "How did Penn's parking policies evolve between the 1960s and 1970s?",
     "compare": true,
     "year_from": 1960,
     "year_to": 1979
    }
   ],
   "answer": "The plans mention that by 1970-71, all resident undergraduate men will be accommodated in University-owned or supervised housing due to the completion of 1,000 additional units [1, (7)]. This suggests that the University's parking policies may have shifted towards providing more on-campus housing to reduce the need for parking.\n\nIn 1977, the University is described as being \"so well within the parking legal requirement, by a margin of 3 to 1\" [8, p. 42], indicating that the University's parking policies may have been more focused on meeting legal requirements rather than addressing the environmental and aesthetic concerns of the campus.\n\nThe 1978-79 plan mentions that the University's policies in areas concerning the future needs of academic facilities, including parking and vehicular circulation, do not exist at Pennsylvania today [11, p. 11]. This suggests that the University's parking policies may have been in a state of flux during the 1970s.\n\nOverall, the plans suggest that Penn's parking policies evolved from a focus on providing more on-campus housing to reduce parking needs in the 1960s to a more laissez-faire approach in the 1970s, with a greater emphasis on meeting legal requirements rather than addressing environmental and aesthetic concerns.",
   "cited": [
    1,
    8,
    11
   ],
   "sources": [
    {
     "n": 1,
     "short": "Development Plan",
     "year": 1961,
     "status": "final",
     "kind": "text",
     "section": "Parking",
     "page_start": 26,
     "page_end": 26,
     "text": "* Figures rounded. (1) University of Pennsylvania Enrollments, Fall Term, 1960, Office of the Registrar. (2) Includes \"Degree,\" \"Certificate,\" and \"Special\" Undergraduate enrollment figures. (3) Residing in University Area (i.e., east of 43rd Street and south of Market Street). (4) Of the 3,000 undergraduate men residing within University Area, 750 are not residing in University owned or supervised housing (i.e., University dormitories or fraternities) (5) It is assumed that new undergraduate men's housing for 300 students will be available by 1965=66. (6) Of the 3,190 undergraduate men projected as residents within the University Area during 1965-66, it is estimated that approximately 675 wil1 not be residing in University owned or supervised housing。 (7) It is assumed that by 1970-7l all resident undergraduate men wil1 be accommodated in University owned or supervised housing due to the completion of 1,000 additional units between 1965 and 1970 within the area bounded by 39/Spruce/40/Walnut Streets. (8) It is assumed that by 1970-71 1,100 additional units will have been completed for undergraduate resident women (600 to complete development of the block bounded by 33/Walnut/34/Chestnut Streets; and the remainder on the block now partially occupied by Sergeant Hal1)."
    },
    {
     "n": 2,
     "short": "Development Plan",
     "year": 1961,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 28,
     "page_end": 28,
     "text": "Total Existing and Projected Essential Off-Street Parking Requirements of University Population and Visitors 1960-61, 1965, and 1970"
    },
    {
     "n": 3,
     "short": "Development Plan",
     "year": 1963,
     "status": "final",
     "kind": "text",
     "section": "Entrances and Exits",
     "page_start": 31,
     "page_end": 31,
     "text": "The University has reviewed the complex of transportation facilities serving the Campus and the present transportation requirements of the faculty, students, administrative personnel, and visitors. The University desires to maintain a balanced system of transportation service to the Campus. Off street parking is one …"
    },
    {
     "n": 4,
     "short": "Development Plan",
     "year": 1963,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 2,
     "page_end": 6,
     "text": "Prepared for presentation to the Philadelphia City Planning Commission and Redevelopment Authority, February 1963 The following report has been prepared for presentation to the Philadelphia City Planning Commission and the Philadelphia Redevelopment Authority. The basis for this report is the University of …"
    },
    {
     "n": 5,
     "short": "Campus Development Plan",
     "year": 1966,
     "status": "final",
     "kind": "text",
     "section": "Parking",
     "page_start": 16,
     "page_end": 16,
     "text": "An analysis cf the University's parking requirements has produced the findings and projections shown in Table 2 by University populaticn group. 1. The information presented in this section has been revised and brought up-to-date by the following dccuments: a. \"The University of Pennsylvania Enrollment Projection …"
    },
    {
     "n": 6,
     "short": "Campus Development Plan",
     "year": 1966,
     "status": "final",
     "kind": "text",
     "section": "Transportation",
     "page_start": 30,
     "page_end": 30,
     "text": "The University has reviewed the complex of transportation facilities serving the Campus and the present transportation requirements of the faculty, students, administrative personnel, and visitors. The University desires to maintain a balanced system of transportation service to the Campus. Off-street parking is one …"
    },
    {
     "n": 7,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "",
     "page_start": 19,
     "page_end": 19,
     "text": "6 Paul Philippe Cret, Warren Powers Laird, Olmsted Brothers, \"Report to the Board of Trustees of the University of Pennsylvania upon the Future Development of Buildings and Grounds and the Conservation of Surrounding Territory\", University of Pennsy1vania, 1913, pp. 13-14. 7 Op. cit. in note 6, p. 8. 8 Op. cit. in …"
    },
    {
     "n": 8,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "PARKING",
     "page_start": 42,
     "page_end": 42,
     "text": "The University is so well within the parking legal requirement, by a margin of 3 to 1, that it does not represent a constraint in the University's overall access program for the foreseeable future. In spatial terms, the area needed for storing one car is equivalent to a classroom size for twenty students, or more than twice the area for an average-sized office. On the other hand, the campus surface parking lots are one of the highest revenue generating operations per dollar invested, and since they are so quickly amortized, are useful as temporary land-banking improvements. From the social perspective, the campus parking facilities and administration service the demand generated by the driving University and University visitor population. To some extent, however, the mere existence of these same parking facilities and their marketing through various mechanisms generates parking demand that would not have otherwise existed (by reason of the economic law of marginal utility). Environmental and aesthetic considerat ons argue against an access program which encourages automobile usage... In sum, since the automobile has assumed such major proportions in the present campus access pattern ... a critical evaluation of its role in the context of an overall campus access program needs to be one of the first priorities... Such an evaluation would be most meaningfully pursued if there were a concurrent exploration of other means for accommodating campus needs\" (op. cit. above, p. 1.3)."
    },
    {
     "n": 9,
     "short": "A Framework for Campus Planning",
     "year": 1978,
     "status": "draft",
     "kind": "text",
     "section": "",
     "page_start": 22,
     "page_end": 35,
     "text": "Wilnut street & Chestnut st 33rd st & 34tm Strect Three times in this century the University of Pennsylvania engaged in an extensive appraisal of its aspirations and achievements. In 1924 President Penniman commissioned the first Educational Survey. President Harnwell, in 1953, commissioned the University's second …"
    },
    {
     "n": 10,
     "short": "A Framework for Campus Planning",
     "year": 1978,
     "status": "draft",
     "kind": "text",
     "section": "",
     "page_start": 36,
     "page_end": 36,
     "text": "Despite these trends, Pennsylvania maintained relative fiscal stability in a time when most major research universities accumulated substantial deficits. To some extent, a shift within our general pattern of expenditures helped to accommodate rising costs. After a slight growth from 1973 to 1975, the number of …"
    },
    {
     "n": 11,
     "short": "Development Plan, Interim Report",
     "year": 1979,
     "status": "draft",
     "kind": "text",
     "section": "Planning Assumptions and Objectives",
     "page_start": 11,
     "page_end": 11,
     "text": "A campus development plan usually attempts to suggest alternative ways for implementing goals and policies already thrashed out within the policy councils of the University. Much of the work of this study has been undertaken with the realization that policies in areas concerning the future needs of academic facilities -- parking and vehicular circulation, recreational facilities, and housing, among others--do not exist at Pennsylvania today, and perhaps cannot exist in the present moment of the University's history. A series of policy assumptions emerged from a variety of meetings Davis, Brody & Associates held with various University administrators:"
    },
    {
     "n": 12,
     "short": "Development Plan, Interim Report",
     "year": 1979,
     "status": "draft",
     "kind": "text",
     "section": "Introduction",
     "page_start": 20,
     "page_end": 20,
     "text": "The:structural changes to the urban fabric of West Philadelphia during this same period yielded equally dramatic consequences. A patchy, sometimes antedated, sometimes vacant City fabric emerged, exhibiting the same pattern of inner City problems other Philadelphia neighborhoods and other urban Universities - Yale, …"
    }
   ]
  },
  {
   "id": "singapore",
   "question": "What did the plans say about building a campus in Singapore?",
   "kind": "Not in the archive",
   "check": "ok",
   "note": "Correct. None of the six passages the search returned mentions Singapore, and the assistant says so instead of answering from general knowledge.",
   "steps": [
    {
     "query": "building a campus in Singapore",
     "compare": false
    }
   ],
   "answer": "The plans do not mention building a campus in Singapore.",
   "cited": [],
   "sources": [
    {
     "n": 1,
     "short": "Campus Development Master Plan",
     "year": 1998,
     "status": "draft",
     "kind": "table",
     "section": "Facilities Services Office of the Architect",
     "page_start": 3,
     "page_end": 3,
     "text": "Campus Development Master Plan Introduction\nExecutive Brief\nContents\nQuotations\nThe Campus in the City\nPrinciples and Philosophies\nSection 3 Campus Precints\nSection 1 Existing Campus Environment\nEast Precinct\nHistory of the Campus South Precinct\nSchools and Academic Precincts Wesy Precinct\nResidences North …"
    },
    {
     "n": 2,
     "short": "Campus Development Plan Reports, 1983–84",
     "year": 1984,
     "status": "final",
     "kind": "text",
     "section": "Introduction",
     "page_start": 54,
     "page_end": 54,
     "text": "as obvious and appropriate when other interests are taken into account。 This \"ideal\" scenario would more readily fit a much less devloped Campus than Pennsylvania's. Here, such a plan is impossible without demolition, extensive relocation, and an increase in the density of building. It would affect the image of the …"
    },
    {
     "n": 3,
     "short": "Landscape Development Plan",
     "year": 1977,
     "status": "final",
     "kind": "text",
     "section": "Introduction",
     "page_start": 6,
     "page_end": 6,
     "text": "A plan is an instrument of growth and change. We avoid the term master plan, which connotes rigidity and finality, and use development plan, which implies orderly growth. Our aim is to define principles on which development can be based and which will allow, and even facilitate, changes of plan in future years. We …"
    },
    {
     "n": 4,
     "short": "Campus Development Master Plan",
     "year": 1998,
     "status": "draft",
     "kind": "text",
     "section": "Key project: Sansom Common",
     "page_start": 88,
     "page_end": 88,
     "text": "Key development projects for the core area of campus locating academic uses to existing Bookstore site near In the summer of 1996, construction began on the Perel- man Quad, a key project for the campus core. Houston, Williams, and Logan Hall, and the Irvine Auditorium will be restored and renovated into a modern …"
    },
    {
     "n": 5,
     "short": "Development Plan",
     "year": 1961,
     "status": "final",
     "kind": "text",
     "section": "Building Space and Campus Area Requirements",
     "page_start": 23,
     "page_end": 24,
     "text": "The University's existing and projected plant requirements have been determined through the work efforts and from the many sources previously cited.2 Each projected square foot building figure has been verified as to its necessity by the responsible head of the activity or functional area concerned. The product …"
    },
    {
     "n": 6,
     "short": "Development Plan, Interim Report",
     "year": 1979,
     "status": "draft",
     "kind": "text",
     "section": "B.2 Problem Buildings and Building Areas",
     "page_start": 33,
     "page_end": 33,
     "text": "Congenial environments need nourishing over time -- the rapid expansion of the campus in the compressed span of fifteen years that came to a close about 1973 carried with it inherent and perhaps inevitable disruptions to the creation of a coherent campus fabric. Fortunately, the problems which exist in some portions …"
    }
   ]
  }
 ]
};
