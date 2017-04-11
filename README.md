# CT_Project
Cell Tower Detection Proposal

    In the past year, the American Civil Liberties Union has identified over 60 agencies in 23 states using “rogue” cell phone sites(1). “Rogue” towers have the ability to collect information about you through the collection of phone metadata, like your cell phone's unique network identifiers. This information can be used for tracking and other nefarious purposes.
    
    In response, the purpose of this project will be to build cell phone tower detectors. Using Raspberry Pis equipped with SIM900 (GSM band module) and GPS chips in specific locations around the university, one can passively detect cell phone tower identification numbers, and the strength of their signal. With this information, one can use a triangulation algorithm to figure out the exact location of a supposed cell phone tower, and then verify it's authenticity. It is also possible to check these IDs against a verified online database to determine if they belong to an authentic tower.
    
    With this project, we hope to answer the following questions:
        1. Are there any “rogue” cell phone towers currently operating in the surrounding area?
        2. If so, what is the best methodology for detecting them?
    The project will also be used as a preliminary step to move into more advanced radio frequency work, including the 2 million dollar DARPA Spectrum Collaboration Challenge(2).

(1): https://www.aclu.org/map/stingray-tracking-devices-whos-got-them
(2): https://spectrumcollaborationchallenge.com/

