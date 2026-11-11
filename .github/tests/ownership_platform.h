#import <Cocoa/Cocoa.h>
#include <ImageIO/ImageIO.h>
#include <CoreServices/CoreServices.h>

@interface OwnershipURL : NSObject {
    NSString *_text;
}
- (id)initWithString:(NSString *)text;
- (NSString *)absoluteString;
@end
@interface OwnershipImage : NSObject
- (id)initWithCGImage:(CGImageRef)image size:(NSSize)size;
- (NSSize)size;
- (CGImageRef)CGImageForProposedRect:(NSRect *)rect context:(id)context hints:(id)hints;
@end
@interface OwnershipButton : NSObject {
    BOOL _enabled;
    OwnershipImage *_image;
}
- (void)setEnabled:(BOOL)value;
- (BOOL)isEnabled;
- (void)setImage:(OwnershipImage *)image;
- (OwnershipImage *)image;
@end
@interface OwnershipWindow : NSObject {
    OwnershipButton *_buttons[5];
    BOOL _edited;
    BOOL _miniaturized;
}
- (OwnershipButton *)standardWindowButton:(NSWindowButton)button;
- (void)setDocumentEdited:(BOOL)value;
- (BOOL)isDocumentEdited;
- (void)setRepresentedURL:(OwnershipURL *)url;
- (void)performMiniaturize:(id)sender;
- (void)deminiaturize:(id)sender;
- (BOOL)isMiniaturized;
@end
CFURLRef OwnershipCreateURL(CFAllocatorRef, CFStringRef, CFURLPathStyle, Boolean);
CFStringRef OwnershipCopyPath(CFURLRef, CFURLPathStyle);
void OwnershipScale(CGContextRef, CGFloat, CGFloat);
void OwnershipTranslate(CGContextRef, CGFloat, CGFloat);
CFMutableDataRef OwnershipData(CFAllocatorRef, CFIndex);
const UInt8 *OwnershipBytes(CFDataRef);
CFIndex OwnershipLength(CFDataRef);
CGImageDestinationRef OwnershipDestination(CFMutableDataRef, CFStringRef, size_t, CFDictionaryRef);
CFMutableDictionaryRef OwnershipDictionary(CFAllocatorRef, CFIndex,
    const CFDictionaryKeyCallBacks *, const CFDictionaryValueCallBacks *);
void OwnershipAddImage(CGImageDestinationRef, CGImageRef, CFDictionaryRef);
bool OwnershipFinalize(CGImageDestinationRef);
void OwnershipRelease(CFTypeRef);

#define NSWindow OwnershipWindow
#define NSButton OwnershipButton
#define NSImage OwnershipImage
#define NSURL OwnershipURL
#define CFURLCreateWithFileSystemPath OwnershipCreateURL
#define CFURLCopyFileSystemPath OwnershipCopyPath
#define CGContextScaleCTM OwnershipScale
#define CGContextTranslateCTM OwnershipTranslate
#define CFDataCreateMutable OwnershipData
#define CFDataGetBytePtr OwnershipBytes
#define CFDataGetLength OwnershipLength
#define CGImageDestinationCreateWithData OwnershipDestination
#define CFDictionaryCreateMutable OwnershipDictionary
#define CGImageDestinationAddImage OwnershipAddImage
#define CGImageDestinationFinalize OwnershipFinalize
#define kUTTypeTIFF CFSTR("synthetic-TIFF")
#define CFRelease OwnershipRelease
