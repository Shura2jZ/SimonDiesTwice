"""
Wrapper minimal autour de Oodle (oo2core) fourni avec Sekiro.

On ne reimplemente PAS Oodle : on appelle la fonction exportee
OodleLZ_Decompress de la DLL fournie par le jeu.

ATTENTION : la signature ci-dessous suit l'API Oodle standard. Si un appel
echoue, c'est le premier endroit a verifier.
"""
import ctypes
import struct

L = ctypes.c_longlong


class Oodle:
    def __init__(self, dll_path: str):
        self.lib = ctypes.WinDLL(dll_path)
        self.lib.OodleLZ_Decompress.restype = L
        self.lib.OodleLZ_Decompress.argtypes = [
            ctypes.c_void_p, L,   # compBuf, compSize
            ctypes.c_void_p, L,   # rawBuf, rawLen
            ctypes.c_int,         # fuzzSafe
            ctypes.c_int,         # checkCRC
            ctypes.c_int,         # verbosity
            ctypes.c_void_p, L,   # decBufBase, decBufSize
            ctypes.c_void_p,      # fpCallback
            ctypes.c_void_p,      # callbackUserData
            ctypes.c_void_p, L,   # decoderMemory, decoderMemorySize
            ctypes.c_int,         # threadPhase
        ]

    # --- compression (ajoute pour M2 : ecrire des DCX moddes) ---
    # OodleLZ_Compressor_Kraken = 8. Niveaux : 4 = Normal, 6 = Optimal2.
    KRAKEN = 8
    LEVEL_NORMAL = 4
    LEVEL_JEU = 6          # valeur lue dans le bloc DCP des fichiers vanilla

    # --- OodleLZ_CompressOptions : structure de 48 octets ---
    #
    # FAIT (deux sources concordantes) :
    #  1. SoulsAssetPipeline/SoulsFormats/Utilities/Compression/Oodle/Oodle.cs
    #     donne l'ordre exact des champs ;
    #  2. la DLL du jeu renvoie une structure identique octet pour octet
    #     (verifie par _work/oodle_probe.py).
    #
    #   +0x00 verbosity             +0x18 spaceSpeedTradeoffBytes
    #   +0x04 minMatchLen           +0x1C maxHuffmansPerChunk
    #   +0x08 seekChunkReset        +0x20 sendQuantumCRCs
    #   +0x0C seekChunkLen          +0x24 maxLocalDictionarySize
    #   +0x10 profile               +0x28 makeLongRangeMatcher
    #   +0x14 dictionarySize        +0x2C matchTableSizeLog2
    OPTIONS_SIZE = 48
    OPTION_SEEK_CHUNK_RESET = 0x08
    OPTION_SEEK_CHUNK_LEN = 0x0C
    SEEK_CHUNK_LEN = 0x40000

    def compressed_size_needed(self, raw_len: int) -> int:
        """Pire cas annonce par Oodle pour une entree de `raw_len` octets.

        FAIT : cette API prend UN SEUL argument (la taille brute), ce que
        confirme SoulsAssetPipeline (Oodle26.cs). L'ancien appel a deux
        arguments renvoyait une valeur absurde (282 pour 16 000 octets).
        """
        self.lib.OodleLZ_GetCompressedBufferSizeNeeded.restype = L
        self.lib.OodleLZ_GetCompressedBufferSizeNeeded.argtypes = [L]
        return self.lib.OodleLZ_GetCompressedBufferSizeNeeded(raw_len)

    def compress(self, src: bytes, compressor: int = KRAKEN, level: int = LEVEL_NORMAL,
                 tranches: bool = True) -> bytes:
        """Compresse en Oodle Kraken et retourne le flux exact.

        ------------------------------------------------------------------
        POINT DECISIF (corrige le 18/10) : le jeu ne lit pas ces flux d'un
        bloc. Il les lit PAR TRANCHES, en s'appuyant sur la table de sauts
        inscrite dans le flux. Un flux sans table de sauts (notre cas
        jusqu'ici) est donc decode en charabia des la 2e tranche -> masse
        brune pour un maillage, plantage pour un squelette.

        Source : SoulsAssetPipeline, Oodle26.cs, qui ecrit des DCX Sekiro
        charges par le jeu :

            options.seekChunkReset = true;   // "Required for the game to not crash"
            options.seekChunkLen   = 0x40000;

        Recoupe par mesure : activer ce seul champ fait passer le fichier
        behbnd de 46 119 a 52 592 octets (le decoupage degrade la
        compression), ce qui prouve que la structure du flux change.
        ------------------------------------------------------------------
        """
        # --- tampon de sortie : pire cas annonce + marge ---
        cap = self.compressed_size_needed(len(src))
        if not (len(src) <= cap <= 4 * len(src) + 0x100000):
            cap = len(src) + len(src) // 4 + 0x100000
        cap += 0x10000

        # --- options : copie de celles par defaut, puis activation des tranches ---
        self.lib.OodleLZ_CompressOptions_GetDefault.restype = ctypes.c_void_p
        self.lib.OodleLZ_CompressOptions_GetDefault.argtypes = [ctypes.c_int, ctypes.c_int]
        p_options = self.lib.OodleLZ_CompressOptions_GetDefault(compressor, level)
        if not p_options:
            raise RuntimeError("OodleLZ_CompressOptions_GetDefault a renvoye NULL")
        options = ctypes.create_string_buffer(
            ctypes.string_at(p_options, self.OPTIONS_SIZE), self.OPTIONS_SIZE)
        if tranches:
            ctypes.memmove(ctypes.addressof(options) + self.OPTION_SEEK_CHUNK_RESET,
                           struct.pack("<i", 1), 4)
            ctypes.memmove(ctypes.addressof(options) + self.OPTION_SEEK_CHUNK_LEN,
                           struct.pack("<i", self.SEEK_CHUNK_LEN), 4)

        srcbuf = ctypes.create_string_buffer(src, len(src))
        dstbuf = ctypes.create_string_buffer(cap)

        # FAIT : OodleLZ_Compress prend 10 arguments (SoulsAssetPipeline,
        # Oodle26.cs). L'ancien appel n'en passait que 9 : le 10e
        # (scratchSize) etait lu dans un registre non initialise.
        self.lib.OodleLZ_Compress.restype = L
        self.lib.OodleLZ_Compress.argtypes = [
            ctypes.c_int,         # compressor
            ctypes.c_void_p, L,   # rawBuf, rawLen
            ctypes.c_void_p,      # compBuf
            ctypes.c_int,         # level
            ctypes.c_void_p,      # pOptions
            ctypes.c_void_p,      # dictionaryBase
            ctypes.c_void_p,      # lrm
            ctypes.c_void_p,      # scratchMem
            L,                    # scratchSize
        ]
        n = self.lib.OodleLZ_Compress(
            compressor, srcbuf, len(src), dstbuf, level,
            options, None, None, None, 0
        )
        if n <= 0:
            raise RuntimeError(f"OodleLZ_Compress a echoue (retour={n})")
        return dstbuf.raw[:n]

    def decompress(self, src: bytes, raw_len: int) -> bytes:
        # FAIT : SoulsAssetPipeline dimensionne le tampon de sortie avec
        # OodleLZ_GetDecodeBufferSize(rawLen, corruptionPossible=true), qui est
        # PLUS GRAND que rawLen. On fait pareil : ecrire raw_len octets pile
        # laisserait le decodeur deborder du tampon.
        self.lib.OodleLZ_GetDecodeBufferSize.restype = L
        self.lib.OodleLZ_GetDecodeBufferSize.argtypes = [L, ctypes.c_int]
        capacite = self.lib.OodleLZ_GetDecodeBufferSize(raw_len, 1)
        if not (raw_len <= capacite <= raw_len + 0x1000000):
            capacite = raw_len + 0x1000
        srcbuf = ctypes.create_string_buffer(src, len(src))
        dstbuf = ctypes.create_string_buffer(capacite)
        n = self.lib.OodleLZ_Decompress(
            srcbuf, len(src),
            dstbuf, raw_len,
            1,  # fuzzSafe     (OodleLZ_FuzzSafe_Yes)
            0,  # checkCRC     (OodleLZ_CheckCRC_No)
            0,  # verbosity
            None, 0,
            None, None,
            None, 0,
            3,  # threadPhase  (OodleLZ_Decode_Unthreaded)
        )
        if n <= 0:
            raise RuntimeError(f"OodleLZ_Decompress a echoue (retour={n})")
        return dstbuf.raw[:n]
