''' These mixins abstract out common fields across workflow engine models.

Several workflow engine models use GenericForeignKey from Django's 
`Content Types Framework <https://docs.djangoproject.com/en/2.2/ref/contrib/contenttypes/>`_.
The use of mixins improves consistency and reduces code duplication in the
associated models that need `Generic Relations <https://docs.djangoproject.com/en/2.2/ref/contrib/contenttypes/#generic-relations>`_.

'''
from .archivable import Archivable
from .configurable import Configurable
from .enqueueable import Enqueueable
from .nameable import Nameable
from .runnable import Runnable
from .stateful import Stateful
from .tagable import Tagable
from .timestamped import Timestamped
from .has_well_known_files import HasWellKnownFiles