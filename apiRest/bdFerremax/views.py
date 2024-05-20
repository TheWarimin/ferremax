from django.shortcuts import render
from rest_framework.decorators import api_view, action
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import viewsets, generics
from .serializer import MarcaSerializer, CustomUserSerializer, CategoriaSerializer, ProductoSerializer, CustomUserSerializer, CarritoSerializer, ProductoCarritoSerializer, ProductoSerializer
from .models import Marca, CustomUser, Categoria, Producto, CustomUser, Carrito, ProductoCarrito, WebpayTransaction, WebpayTransactionItem
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponseRedirect
from transbank.webpay.webpay_plus.transaction import Transaction

class WebpayView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        buy_order = data.get('buy_order')
        session_id = data.get('session_id')
        amount = data.get('amount')
        return_url = data.get('return_url')  # Extraer return_url del cuerpo de la solicitud
        products = data.get('products')  # Extraer la lista de productos de la solicitud

        if not return_url:
            return Response({'error': 'return_url is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = Transaction.create(buy_order, session_id, amount, return_url)  # Pasar return_url a Transaction.create()
        except TypeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Crear una nueva transacción Webpay en la base de datos
        transaction = WebpayTransaction.objects.create(token=response['token'], amount=amount, user_id=data.get('user_id'))
        
        # Procesar cada producto en la lista de productos
        for item in products:
            product = Producto.objects.get(id=item['id'])
            quantity = item['quantity']
            WebpayTransactionItem.objects.create(transaction=transaction, product=product, quantity=quantity)
        
        return Response({'token': response['token']})

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token_ws')  # Obtener el token de la solicitud
        transaction = WebpayTransaction.objects.get(token=token)  # Buscar la transacción por el token
        response = Transaction.commit(token)  # Hacer commit de la transacción con el token
        # Aquí puedes manejar la respuesta de la transacción (por ejemplo, redirigir al usuario a una página de confirmación)
        return Response({'status': response.status, 'amount': transaction.amount})

class WebpayReturnView(APIView):
    def post(self, request, *args, **kwargs):
        token = request.data.get('token_ws')
        response = Transaction.commit(token)
        if response.status == 'AUTHORIZED':
            return Response({"detail": "Transacción autorizada."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Transacción no autorizada."}, status=status.HTTP_400_BAD_REQUEST)


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer 

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class customUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    parser_classes = (MultiPartParser, FormParser)

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer

class ProductoCarritoViewSet(viewsets.ModelViewSet):
    queryset = ProductoCarrito.objects.all()
    serializer_class = ProductoCarritoSerializer

    @action(detail=True, methods=['put'])
    def update_quantity(self, request, pk=None):
        producto_carrito = self.get_object()
        cantidad = request.data.get('cantidad')

        if cantidad is not None:
            producto_carrito.cantidad = cantidad
            producto_carrito.save()
            return Response({'status': 'cantidad actualizada'})
        else:
            return Response({'status': 'cantidad no proporcionada'}, status=status.HTTP_400_BAD_REQUEST)

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class CustomUserCreate(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Todos los campos son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutUserView(APIView):
    def get(self, request):
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    
class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        carrito, created = Carrito.objects.get_or_create(usuario=user)
        producto_id = request.data.get('producto')
        cantidad = request.data.get('cantidad', 1)

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({"detail": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        producto_carrito, created = ProductoCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad}
        )
        if not created:
            producto_carrito.cantidad += cantidad
            producto_carrito.save()

        return Response({"detail": "Producto añadido al carrito."}, status=status.HTTP_200_OK)