"""Шаблон gRPC-сервиса для ДЗ семинара 6.

Основа — gRPC-сервис из семинара 4 (ветка seminar/04-api-interaction-styles).
Сервер слушает порт 50051. Код item_pb2.py / item_pb2_grpc.py сгенерирован
из proto/item.proto (см. README):

    python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/item.proto
"""

from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

import item_pb2
import item_pb2_grpc

PORT = 50051
db={
    "item-1": item_pb2.Item(id="item-1", name="Base Facility", price=10000000.0)
}

class ItemService(item_pb2_grpc.ItemServiceServicer):
    def GetItem(self, request, context):
        if request.id in db:
            return db[request.id]
        else:
          context.abort(grpc.StatusCode.NOT_FOUND, "Item not found")
    def ListItems(self, request, context):
        count = 0
        for item in db.values():
            if request.limit > 0 and count >= request.limit:
                break
            else:
                yield item 
            count += 1
        
    def CreateItems(self, request_iterator, context):
        print(f"Вызван ListItems. Текущая база: {db}")
        created = 0
        for item in request_iterator:
            db[item.id] = item
            created += 1
        return item_pb2.CreateItemsSummary(created_count=created)
        

    def ProcessItems(self, request_iterator, context):
        for item in request_iterator:
            db[item.id] = item
            yield item

def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    item_pb2_grpc.add_ItemServiceServicer_to_server(ItemService(), server)
    service_names = (
        item_pb2.DESCRIPTOR.services_by_name["ItemService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    print(f"gRPC server listening on :{PORT}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
