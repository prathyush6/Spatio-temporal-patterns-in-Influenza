"""
Generate text gurobi output.
"""

import re

class FragmentContainer: # pylint: disable=too-few-public-methods
    """
    Contians sentence fragments.
    """

    def __init__(self, type_, format_, xs):
        self.type = type_
        self.format = format_
        self.xs = xs

    def __str__(self):
        assert self.xs

        if self.xs[0] is None:
            return self.format

        plural_s = "s" if len(self.xs) > 1 else ""

        if len(self.xs) == 1:
            xs = str(self.xs[0])
            return self.format.format(xs, plural_s=plural_s)
        if len(self.xs) == 2:
            xs = f"{self.xs[0]} and {self.xs[1]}"
            return self.format.format(xs, plural_s=plural_s)

        xs_m1 = self.xs[:-1]
        xs_m1 = map(str, xs_m1)
        xs = ", ".join(xs_m1) + f" and {self.xs[-1]}"
        return self.format.format(xs, plural_s=plural_s)

    def __repr__(self):
        return f"FragmentContainer({self.type!r}, {self.format!r}, {self.xs!r})"

def fragment_maker(type_, format_):
    """
    Make fragments.
    """

    def fn(x=None):
        return FragmentContainer(type_, format_, [x])
    return fn

def merge_fragments(xs):
    """
    Merge framgments recursively.
    """

    assert xs

    ret = []
    curx, xs = xs[0], xs[1:]
    for x in xs:
        if (isinstance(curx, FragmentContainer)
                and isinstance(x, FragmentContainer)
                and curx.type == x.type):

            curx.xs.extend(x.xs)
        else:
            if isinstance(curx, FragmentContainer):
                curx.xs = merge_fragments(curx.xs)
            ret.append(curx)
            curx = x

    if isinstance(curx, FragmentContainer):
        curx.xs = merge_fragments(curx.xs)
    ret.append(curx)
    return ret

def merge_states(xss):
    states = []
    rest = []
    for xs in xss:
        if len(xs) == 1 and len(xs[0]) == 2 and xs[0].isupper():
            states.append(xs[0])
        else:
            rest.append(xs)
    if states:
        return [states] + rest
    else:
        return xss

TwoLetterState     = fragment_maker("TowLetterState", "{}")
States             = fragment_maker("States", "states {}")
ThatAre            = fragment_maker("ThatAre", "that are {}")
ThatHad            = fragment_maker("ThatHad", "that had {}")
ThatHaveBeenStable = fragment_maker("ThatHaveBeenStable", "that have been stable")
Where              = fragment_maker("Where", "where {}")
ActivityHas        = fragment_maker("ActivityHas", "activity has {}")
ActivityWas        = fragment_maker("ActivityWas", "activity was {}")
ActivityLevels     = fragment_maker("ActivityLevels", "{} activity levels")
ActivityIsLikelyTo = fragment_maker("ActivityIsLikelyTo", "activity is likely to {}")
BeStable           = fragment_maker("BeStable", "be stable")
ThisWeek           = fragment_maker("ThisWeek", "{} this week")
LastWeek           = fragment_maker("LastWeek", "{} last week")
OneWeekAgo         = fragment_maker("OneWeekAgo", "{} one week ago")
TwoWeeksAgo        = fragment_maker("TwoWeeksAgo", "{} two weeks ago")
ThreeWeeksAgo      = fragment_maker("ThreeWeeksAgo", "{} three weeks ago")
FourWeeksAgo       = fragment_maker("FourWeeksAgo", "{} four weeks ago")
InThe_Region       = fragment_maker("InThe_Region", "in the {} region{plural_s}")
ExpectedToBe       = fragment_maker("ExpectedToBe", "expected to be {}")
FiftyTwoWeeksAgo   = fragment_maker("FiftyTwoWeeksAgo", "{} fifty two weeks ago")

regex_subjects = [
    [
        "(high|low|moderate|minimal)",
        lambda x: States(ThatAre(ExpectedToBe(ThisWeek(x))))
    ],
    [
        "was_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(LastWeek(ActivityLevels(x))))
    ],
    [
        r"was1_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(OneWeekAgo(ActivityLevels(x))))
    ],
    [
        r"was2_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(TwoWeeksAgo(ActivityLevels(x))))
    ],
    [
        r"was3_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(ThreeWeeksAgo(ActivityLevels(x))))
    ],
    [
        r"was4_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(FourWeeksAgo(ActivityLevels(x))))
    ],
    [
        r"was52_(high|low|minimal|moderate)",
        lambda x: States(ThatHad(FiftyTwoWeeksAgo(ActivityLevels(x))))
    ],
]

regex_descriptions = [
    ("(high|low|moderate|minimal)",       lambda x: States(ThatAre(ExpectedToBe(ThisWeek(x))))),
    ("has_been_stable",                   lambda:   States(ThatHaveBeenStable())),
    ("has_(increased|decreased)",         lambda x: States(Where(ActivityHas(x)))),
    ("will_be_stable",                    lambda:   States(Where(ActivityIsLikelyTo(BeStable())))),
    ("will_(decrease|increase)",          lambda x: States(Where(ActivityIsLikelyTo(x)))),
    ("was_(high|low|minimal|moderate)",   lambda x: States(LastWeek(Where(ActivityWas(x))))),
    (r"was1_(high|low|minimal|moderate)", lambda x: States(OneWeekAgo(Where(ActivityWas(x))))),
    (r"was2_(high|low|minimal|moderate)", lambda x: States(TwoWeeksAgo(Where(ActivityWas(x))))),
    (r"was3_(high|low|minimal|moderate)", lambda x: States(ThreeWeeksAgo(Where(ActivityWas(x))))),
    (r"was4_(high|low|minimal|moderate)", lambda x: States(FourWeeksAgo(Where(ActivityWas(x))))),
    (r"was52_(high|low|minimal|moderate)", lambda x: States(FiftyTwoWeeksAgo(Where(ActivityWas(x))))),

    ("NENG", lambda: States(InThe_Region("New England"))),
    ("MEST", lambda: States(InThe_Region("Mideast"))),
    ("GLAK", lambda: States(InThe_Region("Great Lakes"))),
    ("PLNS", lambda: States(InThe_Region("Plains"))),
    ("SEST", lambda: States(InThe_Region("Southeast"))),
    ("SWST", lambda: States(InThe_Region("Southwest"))),
    ("RKMT", lambda: States(InThe_Region("Rocky Mountain"))),
    ("FWST", lambda: States(InThe_Region("Far West"))),

    ("AL",  lambda: TwoLetterState("Alabama")),
    ("AK",  lambda: TwoLetterState("Alaska")),
    ("AZ",  lambda: TwoLetterState("Arizona")),
    ("AR",  lambda: TwoLetterState("Arkansas")),
    ("CA",  lambda: TwoLetterState("California")),
    ("CO",  lambda: TwoLetterState("Colorado")),
    ("CT",  lambda: TwoLetterState("Connecticut")),
    ("DE",  lambda: TwoLetterState("Delaware")),
    ("DC",  lambda: TwoLetterState("District of Columbia")),
    ("FL",  lambda: TwoLetterState("Florida")),
    ("GA",  lambda: TwoLetterState("Georgia")),
    ("HI",  lambda: TwoLetterState("Hawaii")),
    ("ID",  lambda: TwoLetterState("Idaho")),
    ("IL",  lambda: TwoLetterState("Illinois")),
    ("IN",  lambda: TwoLetterState("Indiana")),
    ("IA",  lambda: TwoLetterState("Iowa")),
    ("KS",  lambda: TwoLetterState("Kansas")),
    ("KY",  lambda: TwoLetterState("Kentucky")),
    ("LA",  lambda: TwoLetterState("Louisiana")),
    ("ME",  lambda: TwoLetterState("Maine")),
    ("MD",  lambda: TwoLetterState("Maryland")),
    ("MA",  lambda: TwoLetterState("Massachusetts")),
    ("MI",  lambda: TwoLetterState("Michigan")),
    ("MN",  lambda: TwoLetterState("Minnesota")),
    ("MS",  lambda: TwoLetterState("Mississippi")),
    ("MO",  lambda: TwoLetterState("Missouri")),
    ("MT",  lambda: TwoLetterState("Montana")),
    ("NE",  lambda: TwoLetterState("Nebraska")),
    ("NV",  lambda: TwoLetterState("Nevada")),
    ("NH",  lambda: TwoLetterState("New Hampshire")),
    ("NJ",  lambda: TwoLetterState("New Jersey")),
    ("NM",  lambda: TwoLetterState("New Mexico")),
    ("NY",  lambda: TwoLetterState("New York")),
    ("NC",  lambda: TwoLetterState("North Carolina")),
    ("ND",  lambda: TwoLetterState("North Dakota")),
    ("OH",  lambda: TwoLetterState("Ohio")),
    ("OK",  lambda: TwoLetterState("Oklahoma")),
    ("OR",  lambda: TwoLetterState("Oregon")),
    ("PA",  lambda: TwoLetterState("Pennsylvania")),
    ("RI",  lambda: TwoLetterState("Rhode Island")),
    ("SC",  lambda: TwoLetterState("South Carolina")),
    ("SD",  lambda: TwoLetterState("South Dakota")),
    ("TN",  lambda: TwoLetterState("Tennessee")),
    ("TX",  lambda: TwoLetterState("Texas")),
    ("UT",  lambda: TwoLetterState("Utah")),
    ("VT",  lambda: TwoLetterState("Vermont")),
    ("VA",  lambda: TwoLetterState("Virginia")),
    ("WA",  lambda: TwoLetterState("Washington")),
    ("WV",  lambda: TwoLetterState("West Virginia")),
    ("WI",  lambda: TwoLetterState("Wisconsin")),
    ("WY",  lambda: TwoLetterState("Wyoming")),
    ("PR",  lambda: TwoLetterState("Puerto Rico")),
]

def _expand(x, regexes):
    for regex, replacement in regexes:
        m = re.search(f"^{regex}$", x)
        if m is not None:
            xs = m.groups()
            if callable(replacement):
                return replacement(*xs)
            return replacement
    raise ValueError(f"'{x}' was not matched by any rules")

def expand_subjects(x):
    """
    Expand the subject regexes.
    """

    return _expand(x, regex_subjects)

def expand_descriptions(x):
    """
    Expand the description regexes.
    """

    return _expand(x, regex_descriptions)

def to_text(xss, expandfn):
    xss = merge_states(xss)
    xss = [[expandfn(x) for x in xs] for xs in xss]
    xss = [merge_fragments(xs) for xs in xss]
    xss = [map(str, xs) for xs in xss]
    xss = [" and ".join(xs) for xs in xss]
    xss = ", and ".join(xss)
    return xss

def naive_nlg1(subjects, positives, negatives):
    """
    Generate text from description.
    """

    subjects = to_text([subjects], expand_subjects)
    positives = to_text(positives, expand_descriptions)

    verb = "is"
    if "and" in positives or "states" in positives:
        verb = "are"

    if not negatives:
        return f"{subjects} {verb} {positives}"

    negatives = to_text(negatives, expand_descriptions)
    return f"{subjects} are {positives}, but not {negatives}"
