# Test properties of the sweet-cat database
import pytest


def test_all_have_star_name(SCdata):
    # Test every entry has a "Star" name
    df, _ = SCdata
    assert not df.Star.isnull().values.any()


def test_all_have_link(SCdata):
    # Test each entry has an associated author/paper.
    df, _ = SCdata
    null_links = df.link.isnull()
    # printing is for identifying missing links on failure only
    print("Stars with missing links:\n")
    for star in df.Star[null_links].values:
        print(star)
    assert not null_links.values.any()


# xfail on purpose (to indicate there are missing links only)
@pytest.mark.xfail
def test_links_are_not_self_generated(SCdata):
    # Test if any have exoplanet.eu link from generate_missing_links.
    df, _ = SCdata
    generated_links = df.link.str.contains("http://exoplanet.eu/catalog/")
    print(generated_links)
    # printing is for identifying generated_links on failure only
    print("Stars with artificial links:\n")
    for star in df.Star[generated_links].values:
        print(star)
    assert not generated_links.values.any()


def test_all_have_Author(SCdata):
    # Test each entry has an associated link to paper.
    df, _ = SCdata

    null_author = df.Author.isnull()
    # printing is for identifying missing author on failure only.
    print("Stars with missing Author:")
    for star in df.Star[null_author].values:
        print(star)
    assert not null_author.values.any()
