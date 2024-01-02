from mpi4py import MPI

class MPILogFile(object):
    def __init__(self, comm, filename, mode):
        self.file_handle = MPI.File.Open(comm, filename, mode)
        self.file_handle.Set_atomicity(True)
        self.buffer = bytearray

    def write(self, msg):
        b = bytearray()
        b.extend(map(ord, msg))
        self.file_handle.Write_shared(b)

    def close(self):
        self.file_handle.Sync()
        self.file_handle.Close()