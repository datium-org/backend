import grpc
import grpc_tools.protoc as protoc
from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import message_factory
import importlib
import os

# Function to compile the proto file in-memory and return the necessary descriptors
def load_proto(proto_file):
    proto_path = os.path.dirname(proto_file)
    
    proto_descriptor = descriptor_pb2.FileDescriptorSet()
    protoc.main((
        '',
        f'--proto_path={proto_path}',
        f'--include_imports', 
        f'--descriptor_set_out=/dev/stdout', 
        proto_file
    ), stdout=proto_descriptor)
    
    # Set up descriptor pool and factory
    pool = descriptor_pool.Default()
    for file_descriptor in proto_descriptor.file:
        pool.Add(file_descriptor)
    
    factory = message_factory.MessageFactory(pool)
    
    return pool, factory

# Load the proto file
proto_file = 'example.proto'
pool, factory = load_proto(proto_file)

# Access the descriptors
service_desc = pool.FindServiceByName('example.ExampleService')
method_desc = service_desc.methods_by_name['ExampleMethod']
request_desc = pool.FindMessageTypeByName('example.ExampleRequest')
response_desc = pool.FindMessageTypeByName('example.ExampleResponse')

# Import the generated gRPC modules
grpc_channel = grpc.insecure_channel('localhost:50051')
grpc_stub = grpc.dynamic_stub.DynamicStub(grpc_channel)

# Create request message
request_message = factory.GetPrototype(request_desc)()
request_message.message = 'Hello, gRPC!'

# Make the gRPC call
response_message = grpc_stub._dynamic_method(
    method_desc.full_name,
    request_message,
    response_desc,
)

print(response_message)

# Note: the dynamic_stub module is fictional in this context.
# You'll have to implement a similar dynamic stub that can invoke methods by descriptor.