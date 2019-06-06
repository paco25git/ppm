////////////////////////////////////////////////////////////////////////////////////////////
/// \file		Jai_Error.h
/// \brief		JAI SDK
/// \version	Revison: 1.2.5
/// \author		mat, kic (JAI)
////////////////////////////////////////////////////////////////////////////////////////////
#ifndef _FACTORY_ERROR_H
#define _FACTORY_ERROR_H

  /// Factory status type
  typedef int J_STATUS_TYPE;
  
  /// \brief Error return code enumeration. This is returned by all \c Jai_Factory.dll functions
  typedef enum  
  {
    J_ST_SUCCESS                = 0,      ///< OK      
    J_ST_ERROR                  = -1001,  ///< Generic errorcode
    J_ST_ERR_NOT_INITIALIZED    = -1002,
    J_ST_ERR_NOT_IMPLEMENTED    = -1003,
    J_ST_ERR_RESOURCE_IN_USE    = -1004,
    J_ST_ACCESS_DENIED          = -1005,  ///< Access denied
    J_ST_INVALID_HANDLE         = -1006,  ///< Invalid handle
    J_ST_INVALID_ID             = -1007,  ///< Invalid ID
    J_ST_NO_DATA                = -1008,  ///< No data
    J_ST_INVALID_PARAMETER      = -1009,  ///< Invalid parameter
    J_ST_FILE_IO                = -1010,  ///< File IO error
    J_ST_TIMEOUT                = -1011,  ///< Timeout
    J_ST_ERR_ABORT              = -1012,  /* GenTL v1.1 */
    J_ST_INVALID_BUFFER_SIZE    = -1013,  ///< Invalid buffer size
    J_ST_ERR_NOT_AVAILABLE      = -1014,  /* GenTL v1.2 */
    J_ST_INVALID_ADDRESS        = -1015,  /* GenTL v1.3 */

    J_ST_ERR_CUSTOM_ID          = -10000,
    J_ST_INVALID_FILENAME       = -10001, ///< Invalid file name
    J_ST_GC_ERROR               = -10002, ///< GenICam error. Use \c J_Factory_GetGenICamErrorInfo() to get detailed information
    J_ST_VALIDATION_ERROR       = -10003, ///< Settings File Validation Error. Use \c J_Camera_GetValidationErrorInfo() to get detailed information
    J_ST_VALIDATION_WARNING     = -10004  ///< Settings File Validation Warning. Use \c J_Camera_GetValidationErrorInfo() to get detailed information
  } J_STATUS_CODES;


#endif //_FACTORY_ERROR_H
