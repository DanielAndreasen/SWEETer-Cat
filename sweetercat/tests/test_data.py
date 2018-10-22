# Test properties of the sweet-cat database

def test_all_have_star_name(SCdata):
    # Test every entry has a "Star" name
    df, _ = SCdata
    assert not df.Star.isnull().values.any()


def test_all_have_link(SCdata):
    # Test each entry has an associated author/paper.
    df, _ = SCdata
    null_links = df.link.isnull()
    # Printing is for idenifying missing links on failure only
    print("Stars with missing links:\n")
    for star in df.Star[null_links].values:
        print(star)
    assert not null_links.values.any()


def test_all_have_Author(SCdata):
    # Test each entry has an associated link to paper.
    df, _ = SCdata

    null_author = df.Author.isnull()
    # Printing is for idenifying missing author on failure only.
    print("Stars with missing Author:")
    for star in df.Star[null_author].values:
        print(star)
    assert not null_author.values.any()
