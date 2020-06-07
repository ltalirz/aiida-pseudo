# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Tests for the `PseudoPotentialFamily` class."""
import distutils.dir_util
import os

import pytest

from aiida.common import exceptions

from aiida_pseudo.groups.family.pseudo import PseudoPotentialFamily


def test_type_string():
    """Verify the `_type_string` class attribute is correctly set to the corresponding entry point name."""
    assert PseudoPotentialFamily._type_string == 'pseudo.family'  # pylint: disable=protected-access


@pytest.mark.filterwarnings('ignore:no registered entry point for')
def test_pseudo_type_validation():
    """Test that the constructor raises if `_pseudo_type` is not a subclass of `PseudoPotentialData`."""

    class CustomFamily(PseudoPotentialFamily):
        """Test subclass that intentionally defines incorrect type for `_pseudo_type`."""

        _pseudo_type = int

    with pytest.raises(RuntimeError, match=r'`.*` is not a subclass of `PseudoPotentialData`.'):
        CustomFamily(label='custom')


@pytest.mark.usefixtures('clear_db')
def test_construct():
    """Test the construction of `PseudoPotentialFamily` works."""
    label = 'label'
    family = PseudoPotentialFamily(label=label)
    assert isinstance(family, PseudoPotentialFamily)
    assert not family.is_stored
    assert family.label == label

    label = 'family'
    description = 'description'
    family = PseudoPotentialFamily(label=label, description=description)
    assert isinstance(family, PseudoPotentialFamily)
    assert not family.is_stored
    assert family.label == label
    assert family.description == description


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder(filepath_pseudos):
    """Test the `PseudoPotentialFamily.create_from_folder` class method."""
    label = 'label'
    family = PseudoPotentialFamily.create_from_folder(filepath_pseudos, label)
    assert isinstance(family, PseudoPotentialFamily)
    assert family.is_stored
    assert family.label == label
    assert len(family.nodes) == len(os.listdir(filepath_pseudos))


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder_non_file(tmpdir):
    """Test the `PseudoPotentialFamily.create_from_folder` class method for folder containing a non-file."""
    os.mkdir(os.path.join(str(tmpdir), 'pseudos'))

    with pytest.raises(ValueError, match=r'dirpath `.*` contains at least one entry that is not a file'):
        PseudoPotentialFamily.create_from_folder(str(tmpdir), 'label')


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder_parse_fail(tmpdir):
    """Test the `PseudoPotentialFamily.create_from_folder` class method for file that fails to parse.

    Since the base pseudo potential class cannot really fail to parse, since there is no parsing, this would be
    difficult to test, however, the constructor parses the filename for the element, and that can fail if the filename
    has the incorrect format.
    """
    with open(os.path.join(str(tmpdir), 'Arr.upf'), 'wb'):
        pass

    with pytest.raises(exceptions.ParsingError, match=r'`.*` constructor did not define the element .*'):
        PseudoPotentialFamily.create_from_folder(str(tmpdir), 'label')


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder_empty(tmpdir):
    """Test the `PseudoPotentialFamily.create_from_folder` class method for empty folder."""
    with pytest.raises(ValueError, match=r'no pseudo potentials were parsed from.*'):
        PseudoPotentialFamily.create_from_folder(str(tmpdir), 'label')


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder_duplicate_element(tmpdir, filepath_pseudos):
    """Test the `PseudoPotentialFamily.create_from_folder` class method for folder containing duplicate element."""
    distutils.dir_util.copy_tree(filepath_pseudos, str(tmpdir))

    with open(os.path.join(str(tmpdir), 'Ar.UPF'), 'wb'):
        pass

    with pytest.raises(ValueError, match=r'directory `.*` contains pseudo potentials with duplicate elements'):
        PseudoPotentialFamily.create_from_folder(str(tmpdir), 'label')


@pytest.mark.usefixtures('clear_db')
def test_create_from_folder_duplicate(filepath_pseudos):
    """Test that `PseudoPotentialFamily.create_from_folder` raises for duplicate label."""
    label = 'label'
    PseudoPotentialFamily(label=label).store()

    with pytest.raises(ValueError, match=r'the PseudoPotentialFamily `.*` already exists'):
        PseudoPotentialFamily.create_from_folder(filepath_pseudos, label)


@pytest.mark.usefixtures('clear_db')
def test_add_nodes(get_pseudo_family, get_pseudo_potential_data):
    """Test that `PseudoPotentialFamily.add_nodes` method."""
    family = get_pseudo_family(elements=('Rn',))
    assert family.count() == 1

    pseudos = get_pseudo_potential_data('Ar').store()
    family.add_nodes(pseudos)
    assert family.count() == 2

    pseudos = (get_pseudo_potential_data('Ne').store(),)
    family.add_nodes(pseudos)
    assert family.count() == 3

    pseudos = (get_pseudo_potential_data('He').store(), get_pseudo_potential_data('Kr').store())
    family.add_nodes(pseudos)
    assert family.count() == 5

    # Test for an unstored family
    family = PseudoPotentialFamily(label='label')
    with pytest.raises(exceptions.ModificationNotAllowed):
        family.add_nodes(pseudos)


@pytest.fixture
def nodes_unstored(get_pseudo_potential_data, request):
    """Dynamic fixture returning instances of `PseudoPotentialData` either isolated or as a list."""
    if request.param == 'single':
        return get_pseudo_potential_data()

    if request.param == 'tuple':
        return (get_pseudo_potential_data(),)

    return [get_pseudo_potential_data(), get_pseudo_potential_data('Ne')]


@pytest.mark.usefixtures('clear_db')
@pytest.mark.parametrize('nodes_unstored', ['single', 'tuple', 'list'], indirect=True)
def test_add_nodes_unstored(get_pseudo_family, nodes_unstored):
    """Test that `PseudoPotentialFamily.add_nodes` fails if one or more nodes are unstored."""
    family = get_pseudo_family(elements=('He',))
    count = family.count()

    with pytest.raises(ValueError, match='At least one of the provided nodes is unstored, stopping...'):
        family.add_nodes(nodes_unstored)

    assert family.count() == count


@pytest.fixture
def nodes_incorrect_type(get_pseudo_potential_data, get_upf_data, request):
    """Dynamic fixture returning instances of `UpfData` either isolated or as a list."""
    if request.param == 'single':
        return get_upf_data().store()

    if request.param == 'tuple':
        return (get_upf_data().store(),)

    return [get_pseudo_potential_data().store(), get_upf_data().store()]


@pytest.mark.usefixtures('clear_db')
@pytest.mark.parametrize('nodes_incorrect_type', ['single', 'tuple', 'list'], indirect=True)
def test_add_nodes_incorrect_type(get_pseudo_family, nodes_incorrect_type):
    """Test that `PseudoPotentialFamily.add_nodes` fails if one or more nodes has the incorrect type.

    Even though `UpfData` is a subclass of `PseudoPotentialData` it should still be refused because `add_nodes` checks
    for exact equality of the expected type and does not accept subclasses.
    """
    family = get_pseudo_family()
    count = family.count()

    with pytest.raises(TypeError, match=r'only nodes of type `.*` can be added'):
        family.add_nodes(nodes_incorrect_type)

    assert family.count() == count


@pytest.mark.usefixtures('clear_db')
def test_add_nodes_duplicate_element(get_pseudo_family, get_pseudo_potential_data):
    """Test that `PseudoPotentialFamily.add_nodes` fails if a pseudo is added whose element already exists."""
    family = get_pseudo_family(elements=('Ar',))
    pseudo = get_pseudo_potential_data('Ar').store()

    with pytest.raises(ValueError, match='element `Ar` already present in this family'):
        family.add_nodes(pseudo)


@pytest.mark.usefixtures('clear_db')
def test_pseudos(get_pseudo_potential_data):
    """Test the `PseudoPotentialFamily.pseudos` property."""
    pseudos = {
        'Ar': get_pseudo_potential_data('Ar').store(),
        'He': get_pseudo_potential_data('He').store(),
    }
    family = PseudoPotentialFamily(label='label').store()
    family.add_nodes(list(pseudos.values()))
    assert family.pseudos == pseudos


@pytest.mark.usefixtures('clear_db')
def test_pseudos_mutate(get_pseudo_family, get_pseudo_potential_data):
    """Test that `PseudoPotentialFamily.pseudos` property does not act as a setter."""
    family = get_pseudo_family()

    with pytest.raises(AttributeError):
        family.pseudos = {'He': get_pseudo_potential_data('He')}


@pytest.mark.usefixtures('clear_db')
def test_elements(get_pseudo_family):
    """Test the `PseudoPotentialFamily.elements` property."""
    elements = ['Ar', 'He']
    family = get_pseudo_family(elements=elements)
    assert sorted(family.elements) == elements

    family = PseudoPotentialFamily(label='empty').store()
    assert family.elements == []


@pytest.mark.usefixtures('clear_db')
def test_get_pseudo(get_pseudo_family):
    """Test the `PseudoPotentialFamily.get_pseudo` method."""
    element = 'Ar'
    family = get_pseudo_family(elements=(element,))

    assert family.get_pseudo(element) == family.pseudos[element]

    with pytest.raises(ValueError, match=r'family `.*` does not contain pseudo for element `.*`'):
        family.get_pseudo('He')