from text_generation.annotators.triple_graph import TripleGraph, Node, OBJECT, RELATION
from text_generation.models.document import Document
from text_generation.models.sentence import Sentence
from unittest import TestCase


class TestNode(TestCase):
    def setUp(self):
        self.sentence = Sentence('Mary had a little lamb.')
        self.mary_node = Node('Mary', OBJECT, self.sentence)

    def test_hashing(self):
        mary_node_dup = Node('Mary', OBJECT, self.sentence)

        dict = {self.mary_node, '1'}
        self.assertTrue(mary_node_dup in dict)

    def test_add_child(self):
        # test adding a simple one
        self.mary_node.add_child(Node('had', RELATION, self.sentence))
        self.assertEqual(len(self.mary_node.children), 1)

        # test a duplicate
        duplicate = Node('had', RELATION, self.sentence)
        tree_node = self.mary_node.add_child(duplicate)
        self.assertNotEqual(id(tree_node), id(duplicate))
        self.assertEqual(len(self.mary_node.children), 1)
        self.assertEqual(self.mary_node.children[duplicate], 2)

        # test add an almost duplicate
        almost_duplicate = Node('had', OBJECT, self.sentence)
        self.mary_node.add_child(almost_duplicate)
        self.assertEqual(len(self.mary_node.children), 2)

    def test_is_child(self):
        # test a simple one
        self.mary_node.add_child(Node('had', RELATION, self.sentence))
        self.assertEqual(self.mary_node.is_child_sentence(Node('had', RELATION, self.sentence), self.sentence), True)
        # test a duplicate
        duplicate = Node('had', RELATION, self.sentence)
        self.mary_node.add_child(duplicate)
        self.assertEqual(self.mary_node.is_child_sentence(duplicate, self.sentence), True)
        # test add an almost duplicate
        almost_duplicate = Node('had', OBJECT, self.sentence)
        self.mary_node.add_child(almost_duplicate)
        self.assertEqual(self.mary_node.is_child_sentence(almost_duplicate, self.sentence), True)


    def test_delete_child(self):
        # test delete a simple one
        child = Node('had', RELATION, self.sentence)
        self.mary_node.add_child(child)
        self.assertEqual(len(self.mary_node.children), 1)
        self.assertEqual(self.mary_node.delete_child(child, self.sentence), True)
        self.assertEqual(len(self.mary_node.children), 0)
        # test delete duplicate
        self.mary_node.add_child(child)
        duplicate = Node('had', RELATION, self.sentence)
        self.mary_node.add_child(duplicate)
        self.assertEqual(len(self.mary_node.children), 1)
        self.assertEqual(self.mary_node.children[duplicate], 2)
        self.assertEqual(self.mary_node.delete_child(child, self.sentence), False)
        self.assertEqual(len(self.mary_node.children), 1)
        self.assertEqual(self.mary_node.children[duplicate], 1)

    def test_get_child(self):
        self.mary_node.add_child(Node('had', RELATION, self.sentence))
        almost_duplicate = Node('had', OBJECT, self.sentence)
        self.mary_node.add_child(almost_duplicate)

        duplicate = Node('had', RELATION, self.sentence)
        not_duplicate = self.mary_node.get_child(duplicate)
        self.assertNotEqual(id(duplicate), id(not_duplicate))

    def test_add_sentences(self):
        mary_hadlamb_node = Node('Mari', OBJECT, self.sentence)
        cow_sentence = Sentence('Mary had a cow.')
        mary_hadcow_node = Node('Mari', OBJECT, cow_sentence)

        self.mary_node.add_child(mary_hadlamb_node)
        tree_node = self.mary_node.add_child(mary_hadcow_node)
        self.assertEqual(len(tree_node.sentences), 2)

    def test_merge(self):
        self.mary_node.add_child(Node('had', RELATION, self.sentence))
        self.assertEqual(len(self.mary_node.children), 1)

        cow_sentence = Sentence('Mary had a cow.')
        second_mary = Node('Mary', OBJECT, cow_sentence)

        second_had = Node('had', RELATION, self.sentence)
        cow = second_had.add_child(Node('cow', OBJECT, cow_sentence))
        cow.add_child(Node('deep', OBJECT, cow_sentence))

        second_mary.add_child(second_had)

        second_mary.add_child(Node('child', RELATION, self.sentence))
        self.assertEqual(len(second_mary.children), 2)

        merged_mary = self.mary_node.merge(second_mary)
        self.assertEqual(len(merged_mary.children), 2)


class TestTripleGraph(TestCase):
    def setUp(self):
        self.text_short = """Mary had a little lamb. Its fleece was white as snow.
        Everywhere that Mary went the lamb was sure to go. He followed her to school one day, which was against the rule.
        It made the children laugh and play, to see a lamb at school. And so the teacher turned him out but still he lingered near.
        And waited patiently til Mary did appear. The lamb was sure to go"""

        self.text_long = """Crowdsourced fundraising like GoFundMe puts uncomfortable questions
        into the hands of the giver: Who merits a donation, and how much? Amanda
        Richer turned on the video camera of her cracked, old Samsung and
        started sharing. It was September, and Richer, streaming on Facebook
        Live, talked about living on the outer reaches of The Jungle, Seattle’s
        infamous homeless camp, since last February; about her struggles with
        thoughts of suicide, brought on by repeated brain injuries; and about
        living in a tent under an onramp, where the water was too cold to wash
        her hair. "I’m trying my best, and my best is still here," she said,
        looking around. "I used to be able to do so much better." Project
        Homeless is a Seattle Times initiative that explores the causes of
        homelessness, explains what the Seattle region is doing about it and
        spotlights potential solutions. It is funded by the The Bill & Melinda
        Gates Foundation, Campion Foundation, the Paul G. Allen Family
        Foundation, Raikes Foundation, Schultz Family Foundation, Seattle
        Foundation, Seattle Mariners, and Starbucks. Seattle Times editors and
        reporters operate independently of our funders and maintain editorial
        control over Project Homeless content. · Find out more about Project
        Homeless She had streamed live videos before, but this one struck a
        chord. Mark Horvath, a nationally known blogger on homelessness, reached
        out and filmed a video of Richer that now has over 355,000 views on
        YouTube and more than 3 million on Facebook. Hanes, the clothing
        corporation, featured Richer for their annual sock drive and gave her a
        new phone and data plan to document her life. Richer’s Facebook page has
        more than 20,000 fans, and her live videos about her life are regularly
        seen by thousands. With Horvath’s encouragement, Richer started a
        campaign on GoFundMe, a crowdfunding website. Donations poured in. She
        blew by her goal of $5,000 and has now raised nearly $22,000. Two months
        later, she is still receiving donations by the day, and her life has
        taken a turn for the better. But for every successful campaign like
        Richer’s, there are other pleas that go unanswered. Seattle is littered
        with them. A transgender teen who said he was kicked out by abusive
        parents raised $60 in five months. A volunteer trying to raise $2,500
        for tarps for homeless camps got $715 in two months. A physical
        therapist in Seattle set an ambitious $100,000 campaign called
        "Wheelchairs for Homeless"; it raised nothing in a month. Crowdsourced
        fundraising like GoFundMe puts uncomfortable questions into the hands of
        the giver: Who is worthy of help, and how much? Research suggests
        reaching a fundraising goal depends on how efficient people are at
        marketing their plight. Fundraising consultants are concerned
        crowdfunding sites could take away from charitable giving. Most
        crowdfunding sites are for-profit. GoFundMe takes 2.9 percent as a
        payment-processing fee, plus 30 cents per donation. After the terrorist
        attack at an Ariana Grande concert in England in 2017, two homeless men
        were hailed as heroes when the Guardian reported they rushed in to help.
        But more than $150,000 raised online never reached the men. One couldn’t
        be found. The other was caught on-camera stealing from victims of the
        bombing; donations to him were refunded to donors. Dr. Jeremy Snyder,
        who studies moral obligations toward vulnerable populations at Simon
        Fraser University in British Columbia, argues that crowdfunding is
        actually a symptom of, not a solution to, an unjust society. "You’re
        essentially applying a Band-Aid solution without addressing the
        underlying causes of homelessness," Snyder said. Snyder encourages
        people who want to practice more equitable funding to use nonprofit
        crowdfunding apps like Watsi. Local nonprofit Facing Homelessness has
        started using Classy, which allows donors to pay the processing fee if
        they want to; the nonprofit’s managing director, Sara Vander Zanden,
        said that around 80 percent of donors opt to pay that. On GoFundMe,
        marketing can be everything. The site has a "Fundraiser Tool Kit" with
        articles, written by "Happiness Agents" and "Success Specialists,"
        offering suggestions: Colorful photos liven up the layout. Come up with
        an effective sharing strategy to maximize support. Be specific with
        wish-list items. Add bold headlines to each paragraph, so the story is
        "a breeze" for supporters to read. Chris Kerr, a payroll manager at a
        dialysis center in Federal Way, started a GoFundMe in October for her
        employee, who lost a rental home in Puyallup when a water pipe broke,
        flooding the house. The cleanup exposed mold and asbestos, Kerr said,
        and the family — a single mom with four kids — was ordered to vacate.
        Kerr’s GoFundMe page didn’t include a photo of the woman or her kids, or
        their names. The woman didn’t feel comfortable with it, and Kerr was
        afraid that because the woman was black, she would be stereotyped. The
        campaign raised less than a third of its goal — $1,435. "You’ve got to
        step back and wonder if there are assumptions made because she’s
        homeless and has four kids, and pregnant with a fifth," Kerr said. "A
        lot of people just kind of say, ‘Here we go again, another welfare
        case.’ I do wonder if that, maybe, was part of it." But there were
        problems beyond money. The woman had bad credit, and getting a new
        apartment turned out to be a "huge challenge," Kerr said. Instead, the
        family used the GoFundMe donations to move to South Carolina, where a
        landlord they knew offered a place to stay without a credit check. And
        while money does help, getting someone out of homelessness takes a lot
        more investment — that’s what Richer says when she is asked on Facebook
        how someone can help. "First, talk to that person," Richer said. "Every
        situation is unique." Richer got out of the tent camp and into housing
        on Jan. 30, although she didn’t do it with donations. She got a federal
        housing voucher for an apartment in West Seattle. With unpaid student
        loans and medical bills, finding housing proved much harder for her than
        raising money. Richer said she’s saving most of the GoFundMe money to
        support herself now that she’s housed, so that she can go through
        vocational therapy and mental-health treatment. She signed up for
        disability payments, and is using the donations to live on for now.
        While nearly all the response has been positive, one local advocate
        asked Richer to close her campaign, saying the money she raised was more
        than one person, regardless of need, required to get back on her feet.
        The campaign is still active. And Richer still posts on Facebook. On
        Jan. 30, her move-in date, Richer turned on the phone’s camera to stream
        her and her dog Rowan’s first moments in her new place after living
        outside for more than a year. "This is our home now," she said. "We have
        a home. And it’s over, finally. So thank you. I hope all of you have a
        really great day. Bye." 1. The Professional Claudia Menashe needed
        pictures of sick people. A project director at the National Health
        Museum in Washington, DC, Menashe was putting together a series of
        interactive kiosks devoted to potential pandemics like the avian flu. An
        exhibition designer had created a plan for the kiosk itself, but now
        Menashe was looking for images to accompany the text. Rather than hire a
        photographer to take shots of people suffering from the flu, Menashe
        decided to use preexisting images — stock photography, as it's known in
        the publishing industry. In October 2004, she ran across a stock photo
        collection by Mark Harmel, a freelance photographer living in Manhattan
        Beach, California. Harmel, whose wife is a doctor, specializes in images
        related to the health care industry. "Claudia wanted people sneezing,
        getting immunized, that sort of thing," recalls Harmel, a slight,
        soft-spoken 52-year-old. The National Health Museum has grand plans to
        occupy a spot on the National Mall in Washington by 2012, but for now
        it's a fledgling institution with little money. "They were on a tight
        budget, so I charged them my nonprofit rate," says Harmel, who works out
        of a cozy but crowded office in the back of the house he shares with his
        wife and stepson. He offered the museum a generous discount: $100 to
        $150 per photograph. "That's about half of what a corporate client
        would pay," he says. Menashe was interested in about four shots, so for
        Harmel, this could be a sale worth $600. After several weeks of
        back-and-forth, Menashe emailed Harmel to say that, regretfully, the
        deal was off. "I discovered a stock photo site called iStockphoto," she
        wrote, "which has images at very affordable prices." That was an
        understatement. The same day, Menashe licensed 56 pictures through
        iStockphoto — for about $1 each. iStockphoto, which grew out of a free
        image-sharing exchange used by a group of graphic designers, had
        undercut Harmel by more than 99 percent. How? By creating a marketplace
        for the work of amateur photographers — homemakers, students, engineers,
        dancers. There are now about 22,000 contributors to the site, which
        charges between $1 and $5 per basic image. (Very large, high-resolution
        pictures can cost up to $40.) Unlike professionals, iStockers don't
        need to clear $130,000 a year from their photos just to break even; an
        extra $130 does just fine. "I negotiate my rate all the time," Harmel
        says. "But how can I compete with a dollar?" He can't, of course. For
        Harmel, the harsh economics lesson was clear: The product Harmel offers
        is no longer scarce. Professional-grade cameras now cost less than
        $1,000. With a computer and a copy of Photoshop, even entry-level
        enthusiasts can create photographs rivaling those by professionals like
        Harmel. Add the Internet and powerful search technology, and sharing
        these images with the world becomes simple. At first, the stock industry
        aligned itself against iStockphoto and other so-called microstock
        agencies like ShutterStock and Dreamstime. Then, in February, Getty
        Images, the largest agency by far with more than 30 percent of the
        global market, purchased iStockphoto for $50 million. "If someone's
        going to cannibalize your business, better it be one of your other
        businesses," says Getty CEO Jonathan Klein. iStockphoto's revenue is
        growing by about 14 percent a month and the service is on track to
        license about 10 million images in 2006 — several times what Getty's
        more expensive stock agencies will sell. iStockphoto's clients now
        include bulk photo purchasers like IBM and United Way, as well as the
        small design firms once forced to go to big stock houses. "I was using
        Corbis and Getty, and the image fees came out of my design fees, which
        kept my margin low," notes one UK designer in an email to the company.
        "iStockphoto's micro-payment system has allowed me to increase my
        profit margin." Welcome to the age of the crowd. Just as distributed
        computing projects like UC Berkeley's SETI@home have tapped the unused
        processing power of millions of individual computers, so distributed
        labor networks are using the Internet to exploit the spare processing
        power of millions of human brains. The open source software movement
        proved that a network of passionate, geeky volunteers could write code
        just as well as the highly paid developers at Microsoft or Sun
        Microsystems. Wikipedia showed that the model could be used to create a
        sprawling and surprisingly comprehensive online encyclopedia. And
        companies like eBay and MySpace have built profitable businesses that
        couldn't exist without the contributions of users. All these companies
        grew up in the Internet age and were designed to take advantage of the
        networked world. But now the productive potential of millions of
        plugged-in enthusiasts is attracting the attention of old-line
        businesses, too. For the last decade or so, companies have been looking
        overseas, to India or China, for cheap labor. But now it doesn't matter
        where the laborers are — they might be down the block, they might be in
        Indonesia — as long as they are connected to the network. Technological
        advances in everything from product design software to digital video
        cameras are breaking down the cost barriers that once separated amateurs
        from professionals. Hobbyists, part-timers, and dabblers suddenly have a
        market for their efforts, as smart companies in industries as disparate
        as pharmaceuticals and television discover ways to tap the latent talent
        of the crowd. The labor isn't always free, but it costs a lot less than
        paying traditional employees. It's not outsourcing; it's
        crowdsourcing. It took a while for Harmel to recognize what was
        happening. "When the National Health Museum called, I'd never heard of
        iStockphoto," he says. "But now, I see it as the first hole in the
        dike." In 2000, Harmel made roughly $69,000 from a portfolio of 100
        stock photographs, a tidy addition to what he earned from commissioned
        work. Last year his stock business generated less money — $59,000 — from
        more than 1,000 photos. That's quite a bit more work for less money.
        Harmel isn't the only photographer feeling the pinch. Last summer,
        there was a flurry of complaints on the Stock Artists Alliance online
        forum. "People were noticing a significant decline in returns on their
        stock portfolios," Harmel says. "I can't point to iStockphoto and say
        it's the culprit, but it has definitely put downward pressure on
        prices." As a result, he has decided to shift the focus of his business
        to assignment work. "I just don't see much of a future for professional
        stock photography," he says. VH1 vice president Michael Hirschorn
        created the hit show Web Junk 20& to tap the explosion of homemade
        video. Michael Edwards 2. The Packager "Is that even a real horse? It
        looks like it doesn't have any legs," says Michael Hirschorn, executive
        vice president of original programming and production at VH1 and a
        creator of the cable channel's hit show Web Junk 20. The program
        features the 20 most popular videos making the rounds online in any
        given week. Hirschorn and the rest of the show's staff are gathered in
        the artificial twilight of a VH1 editing room, reviewing their final
        show of the season. The horse in question is named Patches, and it's
        sitting in the passenger seat of a convertible at a McDonald's
        drive-through window. The driver orders a cheeseburger for Patches. "Oh,
        he's definitely real," a producer replies. "We've got footage of him
        drinking beer." The crew breaks into laughter, and Hirschorn asks why
        they're not using that footage. "Standards didn't like it," a producer
        replies. Standards — aka Standards and Practices, the people who decide
        whether a show violates the bounds of taste and decency — had no such
        problem with Elvis the Robocat or the footage of a bicycle racer being
        attacked by spectators and thrown violently from a bridge. Web Junk 20
        brings viewers all that and more, several times a week. In the new,
        democratic age of entertainment by the masses, for the masses, stupid
        pet tricks figure prominently. The show was the first regular program to
        repackage the Internet's funniest home videos, but it won't be the
        last. In February, Bravo launched a series called Outrageous and
        Contagious: Viral Videos, and USA Network has a similar effort in the
        works. The E! series The Soup has a segment called "Cybersmack," and NBC
        has a pilot in development hosted by Carson Daly called Carson Daly's
        Cyberhood, which will attempt to bring beer-drinking farm animals to the
        much larger audiences of network TV. Al Gore's Current TV is placing
        the most faith in the model: More than 30 percent of its programming
        consists of material submitted by viewers. Viral videos are a perfect
        fit for VH1, which knows how to repurpose content to make compelling TV
        on a budget. The channel reinvented itself in 1996 as a purveyor of
        tawdry nostalgia with Pop-Up Video and perfected the form six years
        later with I Love the 80s. "That show was a good model because it got
        great ratings, and we licensed the clips" — quick hits from such
        cultural touchstones as The A-Team and Fatal Attraction — "on the
        cheap," Hirschorn says. (Full disclosure: I once worked for Hirschorn at
        Inside.com.) But the C-list celebrity set soon caught on to VH1's
        searing brand of ridicule. "It started to get more difficult to license
        the clips," says Hirschorn, who has the manner of a laid-back English
        professor. "And we're spending more money now to get them, as our
        ratings have improved." But Hirschorn knew of a source for even more
        affordable clips. He had been watching the growth of video on the
        Internet and figured there had to be a way to build a show around it. "I
        knew we offered something YouTube couldn't: television," he says.
        "Everyone wants to be on TV." At about the same time, VH1's parent
        company, Viacom, purchased iFilm — a popular repository of video clips —
        for $49 million. Just like that, Hirschorn had access to a massive
        supply of viral videos. And because iFilm already ranks videos by
        popularity, the service came with an infrastructure for separating the
        gold from the god-awful. The model's most winning quality, as Hirschorn
        readily admits, is that it's "incredibly cheap" — cheaper by far than
        anything else VH1 produces, which is to say, cheaper than almost
        anything else on television. A single 30-minute episode costs somewhere
        in the mid-five figures — about a tenth of what the channel pays to
        produce so noTORIous, a scripted comedy featuring Tori Spelling that
        premiered in April. And if the model works on a network show like Carson
        Daly's Cyberhood, the savings will be much greater: The average half
        hour of network TV comedy now costs nearly $1 million to produce. Web
        Junk 20 premiered in January, and ratings quickly exceeded even
        Hirschorn's expectations. In its first season, the show is averaging a
        respectable half-million viewers in the desirable 18-to-49 age group,
        which Hirschorn says is up more than 40 percent from the same
        Friday-night time slot last year. The numbers helped persuade the
        network to bring Web Junk 20 back for another season. Hirschorn thinks
        the crowd will be a crucial component of TV 2.0. "I can imagine a time
        when all of our shows will have a user-generated component," he says.
        The channel recently launched Air to the Throne, an online air guitar
        contest, in which viewers serve as both talent pool and jury. The
        winners will be featured during the VH1 Rock Honors show premiering May
        31. Even VH1's anchor program, Best Week Ever, is including clips
        created by viewers. But can the crowd produce enough content to support
        an array of shows over many years? It's something Brian Graden,
        president of entertainment for MTV Music Networks Group, is concerned
        about. "We decided not to do 52 weeks a year of Web Junk, because we
        don't want to burn the thing," he says. Rather than relying exclusively
        on the supply of viral clips, Hirschorn has experimented with soliciting
        viewers to create videos expressly for Web Junk 20. Early results have
        been mixed. Viewers sent in nearly 12,000 videos for the Show Us Your
        Junk contest. "The response rate was fantastic," says Hirschorn as he
        and other staffers sit in the editing room. But, he adds, "almost all of
        them were complete crap." Choosing the winners, in other words, was not
        so difficult. "We had about 20 finalists." But Hirschorn remains
        confident that as user-generated TV matures, the users will become more
        proficient and the networks better at ferreting out the best of the
        best. The sheer force of consumer behavior is on his side. Late last
        year the Pew Internet & American Life Project released a study revealing
        that 57 percent of 12- to 17-year-olds online — 12 million individuals —
        are creating content of some sort and posting it to the Web. "Even if
        the signal-to-noise ratio never improves — which I think it will, by the
        way — that's an awful lot of good material," Hirschorn says. "I'm
        confident that in the end, individual pieces will fail but the model
        will succeed." Engineer Ed Melcarek is one of more than 90,000
        'solvers' working on science problems for corporations. Sandy
        Nicholson 3. The Tinkerer The future of corporate R&D can be found above
        Kelly's Auto Body on Shanty Bay Road in Barrie, Ontario. This is where
        Ed Melcarek, 57, keeps his "weekend crash pad," a one-bedroom apartment
        littered with amplifiers, a guitar, electrical transducers, two desktop
        computers, a trumpet, half of a pontoon boat, and enough electric gizmos
        to stock a RadioShack. On most Saturdays, Melcarek comes in, pours
        himself a St. Remy, lights a Player cigarette, and attacks problems that
        have stumped some of the best corporate scientists at Fortune 100
        companies. Not everyone in the crowd wants to make silly videos. Some
        have the kind of scientific talent and expertise that corporate America
        is now finding a way to tap. In the process, forward-thinking companies
        are changing the face of R&D. Exit the white lab coats; enter Melcarek —
        one of over 90,000 "solvers" who make up the network of scientists on
        InnoCentive, the research world's version of iStockphoto.
        Pharmaceutical maker Eli Lilly funded InnoCentive's launch in 2001 as a
        way to connect with brainpower outside the company — people who could
        help develop drugs and speed them to market. From the outset,
        InnoCentive threw open the doors to other firms eager to access the
        network's trove of ad hoc experts. Companies like Boeing, DuPont, and
        Procter & Gamble now post their most ornery scientific problems on
        InnoCentive's Web site; anyone on InnoCentive's network can take a
        shot at cracking them. The companies — or seekers, in InnoCentive
        parlance — pay solvers anywhere from $10,000 to $100,000 per solution.
        (They also pay InnoCentive a fee to participate.) Jill Panetta,
        InnoCentive's chief scientific officer, says more than 30 percent of
        the problems posted on the site have been cracked, "which is 30 percent
        more than would have been solved using a traditional, in-house
        approach." The solvers are not who you might expect. Many are hobbyists
        working from their proverbial garage, like the University of Dallas
        undergrad who came up with a chemical to use inart restoration, or the
        Cary, North Carolina, patent lawyer who devised a novel way to mix large
        batches of chemical compounds. This shouldn't be surprising, notes
        Karim Lakhani, a lecturer in technology and innovation at MIT, who has
        studied InnoCentive. "The strength of a network like InnoCentive's is
        exactly the diversity of intellectual background," he says. Lakhani and
        his three coauthors surveyed 166 problems posted to InnoCentive from 26
        different firms. "We actually found the odds of a solver's success
        increased in fields in which they had no formal expertise," Lakhani
        says. He has put his finger on a central tenet of network theory, what
        pioneering sociologist Mark Granovetter describes as "the strength of
        weak ties." The most efficient networks are those that link to the
        broadest range of information, knowledge, and experience. Which helps
        explain how Melcarek solved a problem that stumped the in-house
        researchers at Colgate-Palmolive. The giant packaged goods company
        needed a way to inject fluoride powder into a toothpaste tube without it
        dispersing into the surrounding air. Melcarek knew he had a solution by
        the time he'd finished reading the challenge: Impart an electric charge
        to the powder while grounding the tube. The positively charged fluoride
        particles would be attracted to the tube without any significant
        dispersion. "It was really a very simple solution," says Melcarek. Why
        hadn't Colgate thought of it? "They're probably test tube guys without
        any training in physics." Melcarek earned $25,000 for his efforts.
        Paying Colgate-Palmolive's R&D staff to produce the same solution could
        have cost several times that amount — if they even solved it at all.
        Melcarek says he was elated to win. "These are rocket-science
        challenges," he says. "It really reinforced my confidence in what I can
        do." Melcarek, who favors thick sweaters and a floppy fishing hat, has
        charted an unconventional course through the sciences. He spent four
        years earning his master's degree at the world-class particle
        accelerator in Vancouver, British Columbia, but decided against pursuing
        a PhD. "I had an offer from the private sector," he says, then pauses.
        "I really needed the money." A succession of "unsatisfying" engineering
        jobs followed, none of which fully exploited Melcarek's scientific
        training or his need to tinker. "I'm not at my best in a 9-to-5
        environment," he says. Working sporadically, he has designed products
        like heating vents and industrial spray-painting robots. Not every quick
        and curious intellect can land a plum research post at a university or
        privately funded lab. Some must make HVAC systems. For Melcarek,
        InnoCentive has been a ticket out of this scientific backwater. For the
        past three years, he has logged onto the network's Web site a few times
        a week to look at new problems, called challenges. They are categorized
        as either chemistry or biology problems. Melcarek has formal training in
        neither discipline, but he quickly realized this didn't hinder him when
        it came to chemistry. "I saw that a lot of the chemistry challenges
        could be solved using electromechanical processes I was familiar with
        from particle physics," he says. "If I don't know what to do after 30
        minutes of brainstorming, I give up." Besides the fluoride injection
        challenge, Melcarek also successfully came up with a method for
        purifying silicone-based solvents. That challenge paid $10,000. Other
        Melcarek solutions have been close runners-up, and he currently has two
        more up for consideration. "Not bad for a few weeks' work," he says
        with a chuckle. It's also not a bad deal for the companies that can
        turn to the crowd to help curb the rising cost of corporate research.
        "Everyone I talk to is facing a similar issue in regards to R&D," says
        Larry Huston, Procter & Gamble's vice president of innovation and
        knowledge. "Every year research budgets increase at a faster rate than
        sales. The current R&D model is broken." Huston has presided over a
        remarkable about-face at P&G, a company whose corporate culture was once
        so insular it became known as "the Kremlin on the Ohio." By 2000, the
        company's research costs were climbing, while sales remained flat. The
        stock price fell by more than half, and Huston led an effort to reinvent
        the way the company came up with new products. Rather than cut P&G's
        sizable in-house R&D department (which currently employs 9,000 people),
        he decided to change the way they worked. Seeing that the company's
        most successful products were a result of collaboration between
        different divisions, Huston figured that even more cross-pollination
        would be a good thing. Meanwhile, P&G had set a goal of increasing the
        number of innovations acquired from outside its walls from 15 percent to
        50 percent. Six years later, critical components of more than 35 percent
        of the company's initiatives were generated outside P&G. As a result,
        Huston says, R&D productivity is up 60 percent, and the stock has
        returned to five-year highs. "It has changed how we define the
        organ-ization," he says. "We have 9,000 people on our R&D staff and up
        to 1.5 million researchers working through our external networks. The
        line between the two is hard to draw." P&G is one of InnoCentive's
        earliest and best customers, but the company works with other
        crowdsourcing networks as well. YourEncore, for example, allows
        companies to find and hire retired scientists for one-off assignments.
        NineSigma is an online marketplace for innovations, matching seeker
        companies with solvers in a marketplace similar to InnoCentive. "People
        mistake this for outsourcing, which it most definitely is not," Huston
        says. "Outsourcing is when I hire someone to perform a service and they
        do it and that's the end of the relationship. That's not much
        different from the way employment has worked throughout the ages. We're
        talking about bringing people in from outside and involving them in this
        broadly creative, collaborative process. That's a whole new paradigm."
        4. The Masses In the late 1760s, a Hungarian nobleman named Wolfgang von
        Kempelen built the first machine capable of beating a human at chess.
        Called the Turk, von Kempelen's automaton consisted of a small wooden
        cabinet, a chessboard, and the torso of a turbaned mannequin. The Turk
        toured Europe to great acclaim, even besting such luminaries as Benjamin
        Franklin and Napoleon. It was, of course, a hoax. The cabinet hid a
        flesh-and-blood chess master. The Turk was a fancy-looking piece of
        technology that was really powered by human intelligence. Which explains
        why Amazon.com has named its new crowdsourcing engine after von
        Kempelen's contraption. Amazon Mechanical Turk is a Web-based
        marketplace that helps companies find people to perform tasks computers
        are generally lousy at — identifying items in a photograph, skimming
        real estate documents to find identifying information, writing short
        product descriptions, transcribing podcasts. Amazon calls the tasks HITs
        (human intelligence tasks); they're designed to require very little
        time, and consequently they offer very little compensation — most from a
        few cents to a few dollars. InnoCentive and iStockphoto are labor
        markets for specialized talents, but just about anyone possessing basic
        literacy can find something to do on Mechanical Turk. It's
        crowdsourcing for the masses. So far, the program has a mixed track
        record: After an initial burst of activity, the amount of work available
        from requesters — companies offering work on the site — has dropped
        significantly. "It's gotten a little gimpy," says Alan Hatcher, founder
        of Turker Nation, a community forum. "No one's come up with the killer
        app yet." And not all of the Turkers are human: Some would-be workers
        use software as a shortcut to complete the tasks, but the quality
        suffers. "I think half of the people signed up are trying to pull a
        scam," says one requester who asked not to be identified. "There really
        needs to be a way to kick people off the island." Peter Cohen, the
        program's director, acknowledges that Mechanical Turk, launched in beta
        in November, is a work in progress. (Amazon refuses to give a date for
        its official launch.) "This is a very new idea, and it's going to take
        some time for people to wrap their heads around it," Cohen says. "We're
        at the tippy-top of the iceberg." A few companies, however, are already
        taking full advantage of the Turkers. Sunny Gupta runs a software
        company called iConclude just outside Seattle. The firm creates programs
        that streamline tech support tasks for large companies, like Alaska
        Airlines. The basic unit of iConclude's product is the repair flow, a
        set of steps a tech support worker should take to resolve a problem.
        Most problems that iConclude's software addresses aren't complicated
        or time-consuming, Gupta explains. But only people with experience in
        Java and Microsoft systems have the knowledge required to write these
        repair flows. Finding and hiring them is a big and expensive challenge.
        "We had been outsourcing the writing of our repair flows to a firm in
        Boise, Idaho," he says from a small office overlooking a Tully's
        Coffee. "We were paying $2,000 for each one." As soon as Gupta heard
        about Mechanical Turk, he suspected he could use it to find people with
        the sort of tech support background he needed. After a couple of test
        runs, iConclude was able to identify about 80 qualified Turkers, all of
        whom were eager to work on iConclude's HITs. "Two of them had quit
        their jobs to raise their kids," Gupta says. "They might have been
        making six figures in their previous lives, but now they were happy just
        to put their skills to some use." Gupta turns his laptop around to show
        me a flowchart on his screen. "This is what we were paying $2,000 for.
        But this one," he says, "was authored by one of our Turkers." I ask how
        much he paid. His answer: "Five dollars." Contributing editor Jeff Howe
        (jeff_howe@wiredmag.com) wrote about MySpace in issue 13.11. To read
        more about crowdsourcing, please visit Jeff Howe's blog on the subject.
        The Rise of Crowdsourcing 5 Rules of the New Labor Pool Look Who's
        Crowdsourcing', 'Why It Matters Now: With the rise of user-generated
        media such as blogs, Wikipedia, MySpace, and YouTube, it's clear that
        traditional distinctions between producers and consumers are becoming
        blurry. It's no longer fanciful to speak of the marketplace as having a
        "collective intelligence"—today that knowledge, passion, creativity, and
        insight are accessible for all to see. As Time explained after choosing
        the collective "You" as the magazine's 2006 Person of the Year, "We're
        looking at an explosion of productivity and innovation, and it's just
        getting started, as millions of minds that would otherwise have drowned
        in obscurity get backhauled into the global intellectual economy." The
        idea of soliciting customer input is hardly new, of course, and the
        open-source software movement showed that it can be done with large
        numbers of people. The difference is that today's technology makes it
        possible to enlist ever-larger numbers of non-technical people to do
        ever-more complex and creative tasks, at significantly reduced cost. Why
        It Matters to You With a deft touch and a clear set of objectives, quite
        literally thousands of people can and want to help your business. From
        designing ad campaigns to vetting new product ideas to solving difficult
        R&D problems, chances are that people outside your company walls can
        help you perform better in the marketplace; they become one more
        resource you can use to get work done. In return, most participants
        simply want some personal recognition, a sense of community, or at most,
        a financial incentive. The Strong Points Crowdsourcing can improve
        productivity and creativity while minimizing labor and research
        expenses. Using the Internet to solicit feedback from an active and
        passionate community of customers can reduce the amount of time spent
        collecting data through formal focus groups or trend research, while
        also seeding enthusiasm for upcoming products. By involving a cadre of
        customers in key marketing, branding, and product-development processes,
        managers can reduce both staffing costs and the risks associated with
        uncertain marketplace demand. The Weak Spots Crowds are not employees,
        so executives can't expect to control them. Indeed, while they may not
        ask for cash or in-kind products, participants will seek compensation in
        the form of satisfaction, recognition, and freedom. They will also
        demand time, attention, patience, good listening skills, transparency,
        and honesty. For traditional top-down organizations, this shift in
        management culture may prove difficult. Key People Like the concept
        itself, crowdsourcing belongs to no one person, but many have
        contributed to its evolution: Jeff Howe, a contributing editor to Wired
        magazine, first coined the term "crowdsourcing" in a June 2006 article
        and writes the blog crowdsourcing.com. Don Tapscott, a well-known
        business guru, has recently become an evangelist for mass collaboration
        in his book, Wikinomics: How Mass Collaboration Changes Everything. Key
        Practitioners Netflix, the online video rental service, uses
        crowdsourcing techniques to improve the software algorithms used to
        offer customer video recommendations. The team or individual that
        achieves key software goals will receive $1 million. Eli Lily and DuPont
        have tapped online networks of researchers and technical experts,
        awarding cash prizes to people who can solve vexing R&D problems.
        CambrianHouse.com lets the public submit ideas for software products,
        vote on them, and collect royalties if a participant's ideas are
        incorporated into products. iStockphoto.com allows amateur and
        professional photographers, illustrators, and videographers to upload
        their work and earn royalties when their images are bought and
        downloaded. The company was acquired for $50 million by Getty Images.
        Threadless.com lets online members submit T-shirt designs and vote on
        which ones should be produced. How to Talk About It Crowdsourcing
        nomenclature is still in flux, but related terms include: Ideagoras:
        Democratic marketplaces for innovation. Proctor & Gamble taps 90,000
        chemists on Innocentive.com, a forum where scientists collaborate with
        companies to solve R&D problems in return for cash prizes. Prosumers:
        Consumers who have also become producers, creating and building the
        products they use. The hit online game Second Life lets its
        user/residents write and implement software code to improve their
        virtual world. Worksource: Tapping a crowd of people to complete
        repetitive tasks or piecework projects. Amazon's Mechanical Turk is a
        worksource initiative for tasks (such as sorting or classification) that
        are best served by human oversight. Expertsource: A narrower form of
        crowdsourcing that involves soliciting input from technical experts in
        various fields. Further Reading Wikipedia: Written by a crowd of
        contributors, the Wikipedia definition of crowdsourcingincludes many
        examples of companies practicing the concept. Crowdsourcing: A blog by
        Jeff Howe, contributing editor at Wired magazine, who coined the term in
        June 2006. See also: Jeff Howe's Wired magazine article on
        crowdsourcing. CambrianHouse.com press page: Lists new articles written
        globally on crowdsourcing. Wikinomics: How Mass Collaboration Changes
        Everything: A book by Don Tapscott and Anthony D. Williams that offers a
        guide for mass collaboration between customers, suppliers, and
        producers.', 'Fast and efficient data solutions. Complete data tasks
        faster and with greater accuracy than traditional methods. With
        software-based quality-control and proprietary worker reputation
        management, we ensure work is completed with confidence. Quick and easy
        transcription solutions. Transcribe your audio and video content to
        increase exposure and accessibility. We transcribe your audio and video
        files in real-time at a fraction of traditional transcription prices.
        Let our transcription specialists handle your audio and video files fast
        and accurately for more online exposure.', 'The blowback from President
        Obama's interactive town hall has been intense and widespread. In
        dismissing a legitimate policy issue the President seems to have shown
        an uncharacteristic degree of political tone deafness. There are many
        excellent reasons to rethink the War on Drugs—that most ill-fated of
        American conflagrations, and mostly bad ones for staying the course.
        Many in Obama's base felt betrayed by the brush off. And they weren't
        the only ones. A former police chief and mainstream newspaper columnists
        also cried foul. Donations to NORML spiked last week. It's all terribly
        interesting, though not for any of the reasons people think. The
        incident signifies the end of one, increasingly troubled stage in the
        courtship between the President and social media, and — we can only hope
        — the beginning of another, more realistic and mature stage. At this
        critical juncture I'd like to offer some relationship counseling. It's
        perceived by many that the forces of drug reform "hijacked" the White
        House’s Open for Questions platform. Indeed, decriminalization is
        nowhere to be found in any list of what Americans think are the most
        important issues facing the country. But this conclusion assumes the
        technology used by the White House is capable of creating a
        representative sampling of popular opinion. The tech doesn't do that,
        and we shouldn't expect it to. We possess other, highly effective tools
        for that job — they're called polls. Open for Questions fits squarely
        within a genre of crowdsourcing I call "idea jams." These are often
        called suggestion boxes on steroids, or some such silly thing. But in
        reality they constitute their own evolutionary branch of brainstorming.
        Users don’t just submit ideas, but also vote and (usually) comment on
        them as well. Idea jams are a big hit with the private sector. Companies
        like Starbucks, Dell, IBM and even General Mills have all adopted them,
        for the excellent reason that they’re a cost-effective method for
        product innovation, and inspire good will with your customers to boot.
        The best-publicized incarnation involves Dell's "IdeaStorm," which the
        computer maker used to tap its most loyal (or at any rate, most vocal)
        customers. They've now integrated some 280 suggestions into their
        product line. Tellingly, Dell used the same Salesforce.com platform that
        the Obama transition team used to produce the quickly — and justly —
        discarded Citizens' Briefing Book. So if the idea jam format works for
        companies, why isn't it working for our President? A few reasons:
        First, the White House isn't matching the right tool to the right job.
        "The whole point of [such exercises] is not to find the question that
        the whole group wants to ask and that is predictable – but to enable
        cognitive outliers to ask the unpredictable question — to promote ways
        of thinking about problems (and solutions) that are uncommon," writes
        Kim Patrick Kobza, CEO of Neighborhood America, which develops social
        software for business and government. In other words, idea jams are
        built to allow people to discover the fringe question (or idea, or
        solution), then tweak it, discuss it and bring the community's
        attention to it. When Dell launched Idea Storm, it was "hijacked" by
        Linux die-hards which suggested (nay, insisted) that Dell release a
        Linux computer. These folks were "trolls" to the same extent the drug
        legalization lobby swamping White House servers are, and Dell struggled
        with how to deal with them. The company's ultimate reaction is
        instructive. First, they merged all the Linux comments into one thread,
        giving much-needed daylight to other ideas. Next, they saw the value in
        what the Linux folk were saying. The loud and clear demand for an open
        source OS had revealed that there was a "constituency" large enough to
        justify enacting this particular "policy." Put another way, there was
        adequate demand to support a new product line. Three months after
        launch, Dell released three computers pre-installed with Ubuntu. In this
        sense, last week's virtual town hall performed a valuable function. It
        highlighted an important, if non-urgent issue and stimulated an
        ultimately useful public dialogue. The problem was that the President's
        "Director of Participation" wasn't part of that conversation. Which
        brings me to my second point: Participation goes both ways. "Idea
        management is really a three-part process," says Bob Pearson, who as
        Dell's former chief of communities and conversation rode heard on
        IdeaStorm. "The first is listening. That's obvious." The second part,
        Pearson says, was integration, "actually disseminating the best ideas
        throughout our organization. We had engineers studying IdeaStorm posts
        and debating how they could be implemented." The last part is the
        trickiest and most important: "It involves not just enacting the ideas,
        but going back into your community and telling them what you've done."
        Starbucks, which maintains its own version of IdeaStorm, employs 48
        full-time moderators whose only job is to engage the online community.
        In other words, Starbucks is investing the vast share of its resources
        in the second and third parts of the idea management cycle. By contrast,
        the White House essentially used its platform as a listening device, and
        failed to participate in the ensuing conversation. The White House faces
        technological and legal hurdles that Dell and Starbucks don't have to
        worry about, to say nothing of the political considerations of seriously
        entertaining a policy of decriminalization at the very moment when the
        White House most needs GOP votes. If the goal is to allow citizens to
        express themselves, mission accomplished. But if President Obama truly
        wants to engage his constituents in a national conversation, to involve
        them in the hurly-burly of law-making, he'll need to evince a much
        better understanding of how the knowledge, opinions and, yes, wisdom, of
        a large populace can best be harnessed. For one, he could push Google
        Moderator to allow users to comment on each other's ideas. Disabling
        this otherwise standard feature neuters the Idea Jam process from the
        outset. In its current iteration, Open for Questions isn't really
        enabling democracy, unless if by democracy we mean the "never-ending,
        small-bore struggle for advantage among constantly shifting coalitions
        of interest groups," a conception of politics articulated by the early
        20th Century political theorist Arthur Fisher Bentley. This isn’t quite
        as uplifting a vision as the one we were treated to during Barack
        Obama’s campaign, but it may—in the end—be a more realistic one. Cross
        Posted from the Epicenter Blog.', 'Crowdsourcing is the practice of
        engaging a ‘crowd’ or group for a common goal — often innovation,
        problem solving, or efficiency. It is powered by new technologies,
        social media and web 2.0. Crowdsourcing can take place on many different
        levels and across various industries. Thanks to our growing
        connectivity, it is now easier than ever for individuals to collectively
        contribute — whether with ideas, time, expertise, or funds — to a
        project or cause. This collective mobilization is crowdsourcing. This
        phenomenon can provide organizations with access to new ideas and
        solutions, deeper consumer engagement, opportunities for co-creation,
        optimization of tasks, and reduced costs. The Internet and social media
        have brought organizations closer to their stakeholders, laying the
        groundwork for new ways of collaborating and creating value together
        like never before. The approach is being embraced: "Crowds are a hit.
        Millions of people, connected by the Internet, are contributing ideas
        and information to projects big and small. Crowdsourcing, as it is
        called, is helping to solve tricky problems and providing localized
        information. And with the right knowledge, contributing to the crowd —
        and using its wisdom — is easier than ever." -The New York Times
        Changing Environments – Social Media turns into Social Productivity The
        future is human-centric, all about participation and the ability to
        co-create via an increasingly connected world. This new way of doing
        things – crowdsourcing, crowdfunding, co-creation, collaboration, and
        open innovation – is challenging business models and workings of
        organizations across the board, offering an immense opportunity to
        rethink and reinvent conventional processes. Where Can Crowdsourcing Be
        Applied? Crowdsourcing touches across all social and business
        interactions. It is changing the way we work, hire, research, make and
        market. Governments are applying crowdsourcing to empower citizens and
        give a greater voice to the people. In science and health care,
        crowdsourcing can democratize problem solving and accelerate innovation.
        With education, it has the potential to revolutionize the system, just
        as crowdfunding is currently challenging traditional banking and
        investing processes. It’s a 21st-century mindset and approach that can
        be applied in many areas and many ways to:"""

    def test_build_graph(self):
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(self.text_short)
        document.calculate_tf_idf_scores()
        self.graph = TripleGraph(
            document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
        self.assertTrue(self.graph.roots)
        self.assertEqual(len(self.graph.roots[0].children), 1)

        expected = 'mari\n-had\n--lamb\n---wa\n----sure\n---school\n--littl\n---lamb -- VISITED\n\nfleec\n-wa\n--white\n--white\n---as\n----snow\n\nchildren\n-see\n--lamb -- VISITED\n\n'
        self.assertEqual(expected, str(self.graph))


    # TODO this has no assert
    # def test_sentence_ordering(self):
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(
    #         'Two had Three. One had Two. Three had One.'
    #     )
    #     document.calculate_tf_idf_scores()
    #     self.graph = TripleGraph(document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
    #     print(self.graph)
    #     print(self.graph.sentence_ordering_output())

    # TODO this doesn't have any asserts
    # def test_sentence_ordering_0(self):
    #     text_short = """It made the children laugh and play, to see a lamb at school.
    #         And so the teacher turned him out but still he lingered near.
    #         Bob had a dog.
    #         And waited patiently til Mary did appear.
    #         Everywhere that Mary went the lamb was sure to go. He followed her to school one day, which was against the rule.
    #         Mary had a little lamb. Its fleece was white as snow.
    #         The dog was really big.
    #         """
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(text_short)
    #     document.calculate_tf_idf_scores()
    #     document.build_triple_graph()
    #     print(document.graph)
    #     print(document.graph.sentence_ordering_output())


    # TODO this doesn't have any asserts
    # def test_delete_sentence_1(self):
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(
    #         'One had Two. Two had Three. Three had One.'
    #     )
    #     document.calculate_tf_idf_scores()
    #
    #     self.graph = TripleGraph(document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
    #
    #     self.graph.delete_sentence(self.graph.sentences[0])

    # TODO this doesn't have any asserts
    # def test_delete_sentence_2(self):
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(
    #         'One had Two. Two had Three. Three had One.'
    #     )
    #     document.calculate_tf_idf_scores()
    #
    #     self.graph = TripleGraph(document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
    #
    #     self.graph.delete_sentence(self.graph.sentences[1])

    # TODO this doesn't have any asserts
    # def test_delete_sentence_3(self):
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(
    #         'One had Two. Two had Three. Three had One.'
    #     )
    #     document.calculate_tf_idf_scores()
    #
    #     self.graph = TripleGraph(document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
    #
    #     self.graph.delete_sentence(self.graph.sentences[2])


    # TODO this doesn't have any asserts
    # def test_update_tfidf(self):
    #     document = Document.objects.create(title='Mary Short')
    #     document._set_body_sentences(
    #         'One had Two. Two had Three. Three had One.'
    #     )
    #     document.calculate_tf_idf_scores()
    #
    #     self.graph = TripleGraph(document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
    #     print(self.graph._tfidf_scores)
    #     print(document.sentences.all())
    #     self.graph.delete_sentence(self.graph.sentences[2])
    #     document.sentences.filter(text=self.graph.sentences[2].text).delete()
    #     document.calculate_tf_idf_scores()
    #     insert_new_sent = Sentence.objects.create(
    #         text='Two had One.', document=document, position=2)
    #     insert_new_sent.build_triples()
    #     for triple in insert_new_sent.triple_set.all():
    #         self.graph.insert_triple(insert_new_sent, triple)
    #     self.graph.update_tfidf(document.tf_idf_scores)
    #     print(self.graph._tfidf_scores)
    #     print(document.sentences.all())
    #     print(self.graph)


    def test_merge_object(self):
        # subject->relation->object, this tests if the object should hang off something
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'Mary had a little lamb. Phil had a big lamb')
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=0.8)
        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 1)

        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[1])
        self.assertEqual(len(self.graph.roots), 1)

        self.graph.insert_triple(
            document.sentences.all()[1],
            document.sentences.all()[1].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 2)

        # make sure the lamb node is at the same memory location
        mary_lamb = list(list(self.graph.roots[0].children)[0].children)[0]
        phil_lamb = list(list(self.graph.roots[1].children)[0].children)[0]
        self.assertEqual(id(mary_lamb), id(phil_lamb))

    def test_is_reachable(self):
        """Make sure that when Ten had Six that Six is still in the graph."""
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'One had Two. Two had Three. Three had Four. Four had Five. Five had One. Six had Seven. Seven had Eight. Eight had Nine. Nine had Ten. Ten had Six.'
        )
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=0.8)

        for sentence in document.sentences.all():
            self.graph.insert_triple(sentence, sentence.triple_set.all()[0])

        self.assertEqual(len(self.graph.roots), 2)

    def test_merge_cycle(self):
        """Make sure that cycles get merged and all nodes are still reachable (e.g. the roots are not removed)"""
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'One had Two. Two had Three. Three had Four. Four had Five. Five had One. Six had Seven. Seven had Eight. Eight had Nine. Nine had Ten. Ten had Six. Six had Five.'
        )
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=0.8)

        for sentence in document.sentences.all():
            self.graph.insert_triple(sentence, sentence.triple_set.all()[0])

        self.assertEqual(len(self.graph.roots), 2)

    def test_merge_subcycle(self):
        """This should only have one root after Six had One"""
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'One had Two. Two had Three. Three had Four. Four had Five. Five had Three. Six had Seven. Seven had Eight. Eight had Nine. Nine had Ten. Ten had Seven. Six had One.'
        )
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=0.8)

        for sentence in document.sentences.all():
            self.graph.insert_triple(sentence, sentence.triple_set.all()[0])

        self.assertEqual(len(self.graph.roots), 1)

    def test_merge_roots(self):
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'Mary had a little lamb. Phil had a big lamb. Mary likes Phil.')
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=0.8)
        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 1)

        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[1])
        self.assertEqual(len(self.graph.roots), 1)

        self.graph.insert_triple(
            document.sentences.all()[1],
            document.sentences.all()[1].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 2)

        # make sure the lamb node is at the same memory location
        mary_lamb = list(list(self.graph.roots[0].children)[0].children)[0]
        phil_lamb = list(list(self.graph.roots[1].children)[0].children)[0]
        self.assertEqual(id(mary_lamb), id(phil_lamb))

        self.graph.insert_triple(
            document.sentences.all()[2],
            document.sentences.all()[2].triple_set.all()[0])

    def test_pull_apart_tokens(self):
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(
            'Mary had a little lamb. Its fleece was white as snow.')
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph([], document.tf_idf_scores, max_cut=1)
        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[1])
        self.graph.insert_triple(
            document.sentences.all()[0],
            document.sentences.all()[0].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 1)
        self.graph.insert_triple(
            document.sentences.all()[1],
            document.sentences.all()[1].triple_set.all()[0])
        self.assertEqual(len(self.graph.roots), 2)
        self.graph.insert_triple(
            document.sentences.all()[1],
            document.sentences.all()[1].triple_set.all()[1])
        expected = 'mari\n-had\n--littl\n---lamb\n--lamb -- VISITED\n\nfleec\n-wa\n--white\n--white\n---as\n----snow\n\n'
        self.assertEqual(expected, str(self.graph))

    def test_build_big_graph(self):
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(self.text_long)
        document.calculate_tf_idf_scores()

        self.graph = TripleGraph(
            document.sentences.all(), document.tf_idf_scores, max_cut=0.8)
        self.assertEqual(len(self.graph.roots), 178)

    def test_print_graph_plot(self):
        """This is just for printing....uncomment it to run it"""
        self.assertTrue(True)
        # document = Document(self.text_long)
        # document = Document(self.text_short)
        # self.graph = TripleGraph(document.sentences, document.tf_idf_scores, max_cut=0.8)
        # self.graph.plot_graph()

    def test_color_graph(self):
        text_short = """It made the children laugh and play, to see a lamb at school. And so the teacher turned him out but still he lingered near.
        Bob had a dog.
        And waited patiently til Mary did appear.
        Everywhere that Mary went the lamb was sure to go. He followed her to school one day, which was against the rule.
        Mary had a little lamb. Its fleece was white as snow.
        The dog was really big.
        """
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(text_short)
        document.calculate_tf_idf_scores()

        document.build_triple_graph()

        document.graph._color_graph()
        search_color = 3
        eq_color_pairs = list(
            filter(lambda entry: search_color in entry,
                   document.graph._equivalent_colors))
        self.assertEqual(len(eq_color_pairs), 1)
        self.assertEqual(
            [item for sublist in eq_color_pairs for item in sublist], [3, 1])

        eq_colors = [item for sublist in eq_color_pairs for item in sublist]
        color_index = eq_colors.index(search_color)
        eq_colors.pop(color_index)
        self.assertEqual(eq_colors, [1])
        self.assertEqual(eq_colors,
                         document.graph._get_equivalent_colors(search_color))

        self.assertEqual(document.graph._get_equivalent_colors(4), [])

    def test_reorder_roots(self):
        text_short = """It made the children laugh and play, to see a lamb at school. And so the teacher turned him out but still he lingered near.
        Bob had a dog.
        And waited patiently til Mary did appear.
        Everywhere that Mary went the lamb was sure to go. He followed her to school one day, which was against the rule.
        Mary had a little lamb. Its fleece was white as snow.
        The dog was really big.
        """
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(text_short)
        document.calculate_tf_idf_scores()

        document.build_triple_graph()
        document.graph.reorder_roots()

        search_color = 3
        eq_color_pairs = list(
            filter(lambda entry: search_color in entry,
                   document.graph._equivalent_colors))
        self.assertEqual(len(eq_color_pairs), 1)
        self.assertEqual(
            [item for sublist in eq_color_pairs for item in sublist], [3, 1])

        self.assertEqual(str(document.graph.roots[1]), 'mari')
        self.assertEqual(str(document.graph.roots[2]), 'children')

    def test_sentences(self):
        text_short = """It made the children laugh and play, to see a lamb at school.
        And so the teacher turned him out but still he lingered near.
        Bob had a dog.
        And waited patiently til Mary did appear.
        Everywhere that Mary went the lamb was sure to go. He followed her to school one day, which was against the rule.
        Mary had a little lamb. Its fleece was white as snow.
        The dog was really big.
        """
        document = Document.objects.create(title='Mary Short')
        document._set_body_sentences(text_short)
        document.calculate_tf_idf_scores()
        document.build_triple_graph()

        # print(document.graph.roots[0].token)
        # print([sentence.text for sentence in document.graph.roots[0].sentences])

        # print(document.order_sentences())
