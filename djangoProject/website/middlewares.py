from website.utils.cart import Cart


def cart_middleware(get_response):
    def middleware(request):

        response = get_response(request)

        return response

    return middleware
