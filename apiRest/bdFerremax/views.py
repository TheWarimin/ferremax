import random
from rest_framework.decorators import action
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework import viewsets, generics
from .serializer import PedidoSerializer, PedidoSerializer, PedidoProductoSerializer, MetodoPagoSerializer, SucursalSerializer, PedidoSerializer, WebpayTransactionSerializer, WebpayTransactionItemSerializer, MarcaSerializer, CategoriaSerializer, ProductoSerializer, CustomUserSerializer, CarritoSerializer, ProductoCarritoSerializer, ProductoSerializer
from .models import Marca, Categoria, Producto, CustomUser, Carrito, ProductoCarrito, WebpayTransaction, WebpayTransactionItem, Pedido, MetodoPago, Sucursal, ProductoPedido
from .utils import generar_voucher
from django.contrib.auth.models import Group
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from transbank.webpay.webpay_plus.transaction import Transaction
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.core.files import File
from django.http import JsonResponse
from django.views import View
import requests

class UserGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        groups = user.groups.all()
        group_names = [group.name for group in groups]
        return Response({'groups': group_names})

class ValorDolarView(View): #extrae lista la invirte para que parta de la fecha mas reciente y escoje la primera que no sea NaN
    def get(self, request, *args, **kwargs):
        hoy = datetime.now()
        first_date = hoy - timedelta(days=5) 
        first_date_string = first_date.strftime('%Y-%m-%d') 
        url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user=ivostambuk7@gmail.com&pass=2749Ivostambuk&firstdate={first_date_string}&timeseries=F073.TCO.PRE.Z.D&function=GetSeries"
        print(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            observaciones = data['Series']['Obs']
            observaciones.reverse() 
            observacion = next((obs for obs in observaciones if obs['value'] != 'NaN'), None)
            if observacion:
                return JsonResponse({'valor': float(observacion['value'])})
            else:
                return JsonResponse({'error': "No se encontró un valor válido en los últimos 5 días"}, status=404)
        except requests.HTTPError as http_err:
            return JsonResponse({'error': f"Error en la solicitud: {http_err}"}, status=400)
        except Exception as err:
            return JsonResponse({'error': f"Hubo un problema con la solicitud: {err}"}, status=500)

class ValorEuroView(View):
    def get(self, request, *args, **kwargs):
        hoy = datetime.now()
        first_date = hoy - timedelta(days=5) 
        first_date_string = first_date.strftime('%Y-%m-%d') 
        url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user=ivostambuk7@gmail.com&pass=2749Ivostambuk&firstdate={first_date_string}&timeseries=F072.CLP.EUR.N.O.D&function=GetSeries"
        print(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            observaciones = data['Series']['Obs']
            observaciones.reverse() 
            observacion = next((obs for obs in observaciones if obs['value'] != 'NaN'), None)
            if observacion:
                return JsonResponse({'valor': float(observacion['value'])})
            else:
                return JsonResponse({'error': "No se encontró un valor válido en los últimos 5 días"}, status=404)
        except requests.HTTPError as http_err:
            return JsonResponse({'error': f"Error en la solicitud: {http_err}"}, status=400)
        except Exception as err:
            return JsonResponse({'error': f"Hubo un problema con la solicitud: {err}"}, status=500)
        
class ValorArgView(View):
    def get(self, request, *args, **kwargs):
        hoy = datetime.now()
        first_date = hoy - timedelta(days=5) 
        first_date_string = first_date.strftime('%Y-%m-%d') 
        url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user=ivostambuk7@gmail.com&pass=2749Ivostambuk&firstdate={first_date_string}&timeseries=F072.CLP.ARS.N.O.D&function=GetSeries"
        print(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            observaciones = data['Series']['Obs']
            observaciones.reverse() 
            observacion = next((obs for obs in observaciones if obs['value'] != 'NaN'), None)
            if observacion:
                return JsonResponse({'valor': float(observacion['value'])})
            else:
                return JsonResponse({'error': "No se encontró un valor válido en los últimos 5 días"}, status=404)
        except requests.HTTPError as http_err:
            return JsonResponse({'error': f"Error en la solicitud: {http_err}"}, status=400)
        except Exception as err:
            return JsonResponse({'error': f"Hubo un problema con la solicitud: {err}"}, status=500)

class WebpayView(APIView):
    def post(self, request, *args, **kwargs):
        session_id = request.data.get('user_id')
        amount = request.data.get('amount')
        buy_order = str(random.randrange(1000000, 99999999))
        return_url = request.data.get('return_url')
        products = request.data.get('products')
        if not session_id or not amount or not return_url or not products:
            return Response({'error': 'Datos incompletos'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = Transaction().create(buy_order, session_id, amount, return_url)
        except TypeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        transaction, created = WebpayTransaction.objects.get_or_create(
            token=response['token'], defaults={'amount': amount, 'user_id': session_id}
        )
        if not created:
            return Response({'error': 'Transacción duplicada'}, status=status.HTTP_400_BAD_REQUEST)
        for product in products:
            product_instance = get_object_or_404(Producto, id=product['id'])
            WebpayTransactionItem.objects.create(quantity=product['quantity'], transaction=transaction, product=product_instance)
        carrito = get_object_or_404(Carrito, usuario_id=session_id)
        carrito.productocarrito_set.all().delete()
        return Response({
            'retorno_webpay': {
                'url': response['url'],
                'token': response['token']
            }
        })
    
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token_ws')
        try:
            transaction = WebpayTransaction.objects.get(token=token)
            response = Transaction().commit(token)
        except WebpayTransaction.DoesNotExist:
            return Response({'error': 'Transacción no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        transaction_data = WebpayTransactionSerializer(transaction).data
        transaction_data['status'] = response.get('status')
        transaction_data['order_id'] = response.get('buy_order')
        return Response(transaction_data)

class WebpayReturnView(APIView):
    def post(self, request, *args, **kwargs):
        token = request.data.get('token_ws')
        if not token:
            return Response({'error': 'token_ws no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = Transaction().commit(token)
            if response.get('status') == 'AUTHORIZED':
                webpay_transaction = WebpayTransaction.objects.get(token=token)
                webpay_transaction.status = 'AUTHORIZED'
                webpay_transaction.save()
                carrito = Carrito.objects.get(usuario=webpay_transaction.user)
                carrito.productocarrito_set.all().delete()
                return Response({
                    "detail": "Transacción autorizada.",
                    "status": response.get('status'),
                    "amount": response.get('amount'),
                    "buy_order": response.get('buy_order'),
                    "token_ws": token 
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": "Transacción no autorizada.",
                    "status": response.get('status')
                }, status=status.HTTP_400_BAD_REQUEST)
        except WebpayTransaction.DoesNotExist:
            return Response({'error': 'Transacción no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class WebpayTransactionViewSet(viewsets.ModelViewSet):
    queryset = WebpayTransaction.objects.all()
    serializer_class = WebpayTransactionSerializer

class WebpayTransactionItemViewSet(viewsets.ModelViewSet):
    serializer_class = WebpayTransactionItemSerializer
    def get_queryset(self):
        queryset = WebpayTransactionItem.objects.all()
        transaction_id = self.request.query_params.get('transaction_id', None)
        if transaction_id is not None:
            queryset = queryset.filter(transaction_id=transaction_id)
        return queryset

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer 

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class customUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    
    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


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
            user_data = {
                'token': token.key,
                'is_employee': user.is_employee,
                'employee_role': user.employee_role,
            }
            return Response(user_data, status=status.HTTP_200_OK)
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
    
class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer

class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        return Pedido.objects.filter(usuario=usuario)

    def create(self, request, *args, **kwargs):
        usuario = request.user
        carrito = Carrito.objects.get(usuario=usuario)
        productos_carrito = ProductoCarrito.objects.filter(carrito=carrito)

        if not productos_carrito.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        metodo_pago = request.data.get('metodo_pago')
        envio = request.data.get('envio')
        sucursal = request.data.get('sucursal')
        direccion = request.data.get('direccion')
        telefono = request.data.get('telefono')
        total_productos = sum([item.producto.precio * item.cantidad for item in productos_carrito])
        costo_envio = 3000 if envio == 'domicilio' else 0
        total = total_productos + costo_envio

        pedido_data = {
            'usuario': usuario.id,
            'metodo_pago': metodo_pago,
            'envio': envio,
            'sucursal': sucursal,
            'direccion': direccion if envio == 'domicilio' else None,
            'telefono': telefono if envio == 'domicilio' else None,
            'total': total,
            'productos': [{'producto_id': item.producto.id, 'cantidad': item.cantidad} for item in productos_carrito]
        }

        serializer = self.get_serializer(data=pedido_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        pedido = serializer.instance

        for item in productos_carrito:
            ProductoPedido.objects.create(pedido=pedido, producto=item.producto, cantidad=item.cantidad)

        ruta_voucher = generar_voucher(pedido)
        pedido.voucher = ruta_voucher
        pedido.save()

        productos_carrito.delete()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AdminPedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.all()

    def create(self, request, *args, **kwargs):
        usuario = request.user
        carrito = Carrito.objects.get(usuario=usuario)
        productos_carrito = ProductoCarrito.objects.filter(carrito=carrito)

        if not productos_carrito.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        metodo_pago = request.data.get('metodo_pago')
        envio = request.data.get('envio')
        sucursal = request.data.get('sucursal')
        direccion = request.data.get('direccion')
        telefono = request.data.get('telefono')
        total_productos = sum([item.producto.precio * item.cantidad for item in productos_carrito])
        costo_envio = 3000 if envio == 'domicilio' else 0
        total = total_productos + costo_envio

        pedido_data = {
            'usuario': usuario.id,
            'metodo_pago': metodo_pago,
            'envio': envio,
            'sucursal': sucursal,
            'direccion': direccion if envio == 'domicilio' else None,
            'telefono': telefono if envio == 'domicilio' else None,
            'total': total,
            'productos': [{'producto_id': item.producto.id, 'cantidad': item.cantidad} for item in productos_carrito]
        }

        serializer = self.get_serializer(data=pedido_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        pedido = serializer.instance

        for item in productos_carrito:
            ProductoPedido.objects.create(pedido=pedido, producto=item.producto, cantidad=item.cantidad)

        ruta_voucher = generar_voucher(pedido)
        pedido.voucher = ruta_voucher
        pedido.save()

        productos_carrito.delete()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserPedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        return Pedido.objects.filter(usuario=usuario)

    def create(self, request, *args, **kwargs):
        usuario = request.user
        carrito = Carrito.objects.get(usuario=usuario)
        productos_carrito = ProductoCarrito.objects.filter(carrito=carrito)

        if not productos_carrito.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        metodo_pago = request.data.get('metodo_pago')
        envio = request.data.get('envio')
        sucursal = request.data.get('sucursal')
        direccion = request.data.get('direccion')
        telefono = request.data.get('telefono')
        total_productos = sum([item.producto.precio * item.cantidad for item in productos_carrito])
        costo_envio = 3000 if envio == 'domicilio' else 0
        total = total_productos + costo_envio

        pedido_data = {
            'usuario': usuario.id,
            'metodo_pago': metodo_pago,
            'envio': envio,
            'sucursal': sucursal,
            'direccion': direccion if envio == 'domicilio' else None,
            'telefono': telefono if envio == 'domicilio' else None,
            'total': total,
            'productos': [{'producto_id': item.producto.id, 'cantidad': item.cantidad} for item in productos_carrito]
        }

        serializer = self.get_serializer(data=pedido_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        pedido = serializer.instance

        for item in productos_carrito:
            ProductoPedido.objects.create(pedido=pedido, producto=item.producto, cantidad=item.cantidad)

        ruta_voucher = generar_voucher(pedido)
        pedido.voucher = ruta_voucher
        pedido.save()

        productos_carrito.delete()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
