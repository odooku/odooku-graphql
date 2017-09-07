from odooku.patch import SoftPatch


class patch_root(SoftPatch):

    @staticmethod
    def apply_patch():

        from odooku.patch.helpers import patch_class

        @patch_class(globals()['Root'])
        class Root(object):

            def get_request(self, httprequest):
                if httprequest.path == '/graphql':
                    return HttpRequest(httprequest)
                return self.get_request_(httprequest)

        root = Root()
        return locals()


patch_root('odoo.http')