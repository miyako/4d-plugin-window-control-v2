// Syntax-only helper branches; not a Windows SDK or ABI substitute.
#include "4DPlugin-Window-Control.h"
#include "ARRAY_TEXT.h"
#include "C_BLOB.h"
#include "C_LONGINT.h"
#include "4DPlugin-JSON.h"
#include <cstring>
#include <cwchar>
#include <cstdlib>
#undef VERSIONMAC
#undef VERSIONWIN
#define VERSIONMAC 0
#define VERSIONWIN 1
#define _WIN32 1
using LPCWSTR = const wchar_t*;
using LPWSTR = wchar_t*;
using LPCSTR = const char*;
using LPSTR = char*;
enum { CP_UTF8 = 65001 };
[[noreturn]] inline void OwnershipUnexpectedWindows() { std::abort(); }
inline int MultiByteToWideChar(unsigned, unsigned, LPCSTR, int, LPWSTR, int) { OwnershipUnexpectedWindows(); }
inline int WideCharToMultiByte(unsigned, unsigned, LPCWSTR, int, LPSTR, int, LPCSTR, BOOL*) { OwnershipUnexpectedWindows(); }
inline int sprintf_s(char*, size_t, const char*, unsigned) { OwnershipUnexpectedWindows(); }
