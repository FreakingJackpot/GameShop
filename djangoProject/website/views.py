from http import HTTPStatus

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View

from .forms import OrderEmailForm
from .models import Game, GameImage
from .tasks import order_process
from .utils.cart import Cart


class HomeView(View):
    paginate_by = 3

    def get(self, request, *args, **kwargs):
        queryset = Game.get_obj_for_list_view()

        game_name_query = request.GET.get('query')
        if game_name_query:
            queryset = queryset.filter(name__trigram_word_similar=game_name_query)

        page_num = request.GET.get('page', 1)
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.page(page_num)

        header_by_id = {i.game_id: i.url for i in GameImage.objects.filter(game__in=queryset, is_header=True)}

        games = [{'obj': game, 'header': header_by_id[game.id], 'genres': ', '.join(g.name for g in game.genres.all())}
                 for
                 game
                 in page_obj]
        context = {
            'games': games,
            'page_obj': page_obj,
            'content_block_name': f'Результаты по поиску: "{game_name_query}"' if game_name_query else "Все игры"
        }

        return render(request, 'website/home.html', context)


class DetailView(View):
    template_name = 'website/detail.html'

    def get(self, request, *args, **kwargs):
        game = Game.obj_by_pk(kwargs['game_id'])

        images = list(GameImage.objects.filter(game=game))

        for i, image in enumerate(images):
            if image.is_header:
                header = images.pop(i)

        req_min, req_recom = game.requirements.split('\n')
        req_min = req_min.replace("<strong>Минимальные:</strong><br>", "")
        req_recom = req_recom.replace("<strong>Рекомендованные:</strong><br>", "")

        game = {
            'obj': game,
            'header': header,
            'images': images,
            'req_min': req_min,
            'req_recom': req_recom,
            'diff_in_price': game.price - game.discount_price if game.discount_price else None,

        }

        return render(request, 'website/detail.html', {'game': game, })


class CartView(View):
    def post(self, request, *args, **kwargs):
        quantity = int(request.POST.get('quantity'))
        game_id = int(request.POST.get('game_id'))

        cart = Cart(request.session)
        cart.handle_request(game_id, quantity)

        return HttpResponse(status=HTTPStatus.OK)


class OrderView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'website/order.html')

    def post(self, request, *args, **kwargs):
        form = OrderEmailForm(request.POST)
        if form.is_valid():
            cart = Cart(request.session)
            order_process.delay(form.cleaned_data['email'], cart.to_dict())
            cart.flush()
            return redirect('website:home')
        else:
            return render(request, 'website/order.html', {'form': form})
