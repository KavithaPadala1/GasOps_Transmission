SQL = """select 
			TransmissionWorkOrderID,
			ProjectNumber,
			WorkOrderNumber,
			WeldSerialNumber,
			ISNULL(IsCutOut,'') as IsCutOut,
			ISNULL(IsRepairedDesc,'') as IsRepaired,
			CASE WHEN ISNULL(IsCutOut,'')='YES' then 'CutOut'
				 WHEN ISNULL(IsRepairedDesc,'')='Yes' then 'Repaired'
				 ELSE 'Production' end as WeldCategory,
			ISNULL(WeldingContractorName,'') as WeldingContractorName,
			ISNULL(CWIContractorName,'') as ContractorCWIName,
			ISNULL(CWIInspectorName,'') as CWIName,
			ISNULL(PartiallyCompleted,'') as Completed,
			CASE WHEN ISNULL(PartiallyCompleted,'')='Yes' then ISNULL(WeldCompletionDateTime,'')
				 ELSE '' end as WeldCompletionDateTime,			
			ISNULL(VisualInspResult,'') as CWIResult,
			IsUnlocked,
			isnull(Welder1ITSID,'') as Welder1ITSID,
			isnull(Welder2ITSID,'') as Welder2ITSID,
			isnull(Welder3ITSID,'') as Welder3ITSID,
			isnull(Welder4ITSID,'') as Welder4ITSID,
			isnull(Welder1Name,'') as Welder1Name,
			isnull(Welder2Name,'') as Welder2Name,
			isnull(Welder3Name,'') as Welder3Name,
			isnull(Welder4Name,'') as Welder4Name,
			ISNULL(SegCompFieldID1,'') as HeatSerialNumber1,
			ISNULL(Heat1Description,'') as Heat1Description,
			ISNULL(SegCompFieldID2,'') as HeatSerialNumber2,
			ISNULL(Heat2Description,'') as Heat2Description,
			ISNULL(RootRodClass,'') as RootRodClass,
			ISNULL(RootLotNumber,'') as RootLotNumber,
			ISNULL(HotRodClass,'') as HotRodClass,
			ISNULL(HotLotNumber,'') as HotLotNumber,
			ISNULL(FillerRodClass,'') as FillerRodClass,
			ISNULL(FillerLotNumber,'') as FillerLotNumber,
			ISNULL(CapRodClass,'') as CapRodClass,
			ISNULL(CapLotNumber,'') as CapLotNumber,
			ISNULL(PreHeat,'') as PreHeat,
			ISNULL(Temperature,'') as Temperature,
			ISNULL(TieInWeld,'') as TieinWeld,
			ISNULL(Prefab,'') as Prefab,
			ISNULL(Alignment,'') as Alignment,
			ISNULL(Gap,'') as Gap,
			ISNULL(FinalWeld,'') as FinalWeld,
			ISNULL(WeldingProcess,'') as WeldingProcess,
			ISNULL(JointFitUp,'') as JointFitUp,
			ISNULL(LineupClamp,'') as LineupClamp,
			ISNULL(PreweldCleanliness,'') as PreweldCleanliness,
			ISNULL(MiterJoint,'') as MiterJoint,
			ISNULL(Degrees,'') as MitterDegrees,
			ISNULL(Tacks,'') as Tacks,
			ISNULL(RootPass,'') as RootPass,
			ISNULL(InsideAccess,'') as InsideAccess,
			ISNULL(InsideInspected,'') as InsideInspected,
			ISNULL(SubfillPasses,'') as SubfillPasses,
			ISNULL(CapHP,'') as CapHP,
			ISNULL(Comments,'') as Comments,
			ISNULL(AddedtoWeldMap,'') as AddedtoWeldMap,
			CASE WHEN isnull((select top 1 RTInspectionID from FWRTInspectionDetails where FieldWeldID=TransmissionISOMainJointID and IsDeleted=0),0)<>0 then 'Yes'
				 WHEN isnull((select top 1 CMPRRTInspectionID from FWCMPRRTInspectionDetails where FieldWeldID=TransmissionISOMainJointID and IsDeleted=0),0)<>0 then 'Yes'
				 WHEN isnull((select top 1 DIGRRTInspectionID from FWDIGRRTInspectionDetails where FieldWeldID=TransmissionISOMainJointID and IsDeleted=0),0)<>0 then 'Yes'
				 Else 'No' end as HasNDEReport,	 
			ISNULL(NDEContractorName,'') as NDEContractorName,
			ISNULL(NDEInspectorName,'') as NDEInspectorName,
			ISNULL(RadiographedDateDT,'') as RadiographedDateDT,
			ISNULL(RTReportNumber,'') as RTReportNumber,
			ISNULL(RTReportNumberandType,'') as NDEReportNumber,
			ISNULL(NDEStatus,'') as NDEStatus,
			ISNULL(NDECompletionDate,'') as NDECompletionDate,
			ISNULL(CRIContractorName,'') as CRIContractorName,
			ISNULL(CRIInspectorName,'') as CRIInspectorName,
			ISNULL(CRIStatus,'') as CRIStatus,
			ISNULL(CRICompletionDate,'') as CRICompletionDate,
			ISNULL(TRCrew,'') as TRContractorName,
			ISNULL(TRName,'') as TRName,
			ISNULL(TRStatus,'') as TRStatus,
			ISNULL(TRCompletionDate,'') as TRCompletionDate
			from
			(SELECT distinct WO.TransmissionWorkOrderID,IJ.TransmissionISOMainJointID,
				WO.WorkOrderNo as WorkOrderNumber,WO.JobNumber as ProjectNumber,
				CASE WHEN WO.CrewType=2 THEN CM.ContractorDisplayName
					 WHEN WO.CrewType=1 THEN 'Company'
					 ELSE '' END as WeldingContractorName,
				IJ.JointID as WeldSerialNumber,convert(nvarchar,IJ.CreatedDate,101) as WeldStartDateDT,CONVERT(nvarchar,IJ.WeldCompletionDateTime,101) as WeldCompletionDateTime,
				CMC.ContractorDisplayName as CWIContractorName,
				isnull((select CWIName from TransmissionISOMainJointSignature IJS where IJS.TransmissionISOMainJointID=IJ.TransmissionISOMainJointID and IJS.IsActive=1),'') as CWIInspectorName,
				CASE WHEN ISNULL(IJ.IsRepaired,0)=1 then 'YES'  
					 ELSE '' END as IsRepairedDesc,IJ.IsCutOut,
				IJ.SegCompFieldID1,
				CASE WHEN ISNULL(IJ.SegCompField1MTRFileID,0)<>0 THEN (SELECT top 1 ISNULL(AM.AssetCategoryDescription,'') + ';;' + ISNULL(ASM.SubCategoryDescription,'')+ ';;' + ISNULL(MM.MaterialDescription,'') + ';;' + ISNULL(SM.SizeDescription,'') + ';;' + ISNULL(MFM.ManufacturerName,'') as Heat1Description
																	 FROM CompanyMTRFile MF  
																	 LEFT JOIN AssetCategoryMaster AM on AM.AssetCategoryID=MF.AssetCategoryID  
																	 LEFT JOIN AssetSubCategoryMaster ASM on ASM.AssetSubCategoryID=MF.AssetSubCategoryID  
																	 LEFT JOIN MaterialMaster MM on MM.MaterialID=MF.MaterialID  
																	 LEFT JOIN SizeMaster SM on SM.SizeID=MF.SizeID  
																	 LEFT JOIN ManufacturerMaster MFM on MFM.ManufacturerID=MF.ManufacturerID  
																	 WHERE MF.CompanyMTRFileID=IJ.SegCompField1MTRFileID)
					 WHEN ISNULL(IJ.SegCompFieldID1,'')<>'' THEN (SELECT top 1 ISNULL(AM.AssetCategoryDescription,'') + ';;' + ISNULL(ASM.SubCategoryDescription,'')+ ';;' + ISNULL(MM.MaterialDescription,'') + ';;' + ISNULL(SM.SizeDescription,'') + ';;' + ISNULL(MFM.ManufacturerName,'') as Heat1Description
																	 FROM CompanyMTRFile MF  
																	 LEFT JOIN AssetCategoryMaster AM on AM.AssetCategoryID=MF.AssetCategoryID  
																	 LEFT JOIN AssetSubCategoryMaster ASM on ASM.AssetSubCategoryID=MF.AssetSubCategoryID  
																	 LEFT JOIN MaterialMaster MM on MM.MaterialID=MF.MaterialID  
																	 LEFT JOIN SizeMaster SM on SM.SizeID=MF.SizeID  
																	 LEFT JOIN ManufacturerMaster MFM on MFM.ManufacturerID=MF.ManufacturerID  
																	 WHERE MF.IsActive=1 and (RTRIM(LTRIM(IJ.SegCompFieldID1)) in (select items from dbo.Split(MF.HeatNumber,';')) or MF.SerialNumber=RTRIM(LTRIM(IJ.SegCompFieldID1))))
					ELSE '' END as Heat1Description,
				IJ.SegCompFieldID2,
				CASE WHEN ISNULL(IJ.SegCompField2MTRFileID,0)<>0 THEN (SELECT top 1 ISNULL(AM.AssetCategoryDescription,'') + ';;' + ISNULL(ASM.SubCategoryDescription,'')+ ';;' + ISNULL(MM.MaterialDescription,'') + ';;' + ISNULL(SM.SizeDescription,'') + ';;' + ISNULL(MFM.ManufacturerName,'') as Heat2Description
																	 FROM CompanyMTRFile MF  
																	 LEFT JOIN AssetCategoryMaster AM on AM.AssetCategoryID=MF.AssetCategoryID  
																	 LEFT JOIN AssetSubCategoryMaster ASM on ASM.AssetSubCategoryID=MF.AssetSubCategoryID  
																	 LEFT JOIN MaterialMaster MM on MM.MaterialID=MF.MaterialID  
																	 LEFT JOIN SizeMaster SM on SM.SizeID=MF.SizeID  
																	 LEFT JOIN ManufacturerMaster MFM on MFM.ManufacturerID=MF.ManufacturerID  
																	 WHERE MF.CompanyMTRFileID=IJ.SegCompField2MTRFileID)
					 WHEN ISNULL(IJ.SegCompFieldID2,'')<>'' THEN (SELECT top 1 ISNULL(AM.AssetCategoryDescription,'') + ';;' + ISNULL(ASM.SubCategoryDescription,'')+ ';;' + ISNULL(MM.MaterialDescription,'') + ';;' + ISNULL(SM.SizeDescription,'') + ';;' + ISNULL(MFM.ManufacturerName,'') as Heat2Description
																	 FROM CompanyMTRFile MF  
																	 LEFT JOIN AssetCategoryMaster AM on AM.AssetCategoryID=MF.AssetCategoryID  
																	 LEFT JOIN AssetSubCategoryMaster ASM on ASM.AssetSubCategoryID=MF.AssetSubCategoryID  
																	 LEFT JOIN MaterialMaster MM on MM.MaterialID=MF.MaterialID  
																	 LEFT JOIN SizeMaster SM on SM.SizeID=MF.SizeID  
																	 LEFT JOIN ManufacturerMaster MFM on MFM.ManufacturerID=MF.ManufacturerID  
																	 WHERE MF.IsActive=1 and (RTRIM(LTRIM(IJ.SegCompFieldID2)) in (select items from dbo.Split(MF.HeatNumber,';')) or MF.SerialNumber=RTRIM(LTRIM(IJ.SegCompFieldID2))))
					ELSE '' END as Heat2Description,
				TWT.Content as WeldTypeDesc,
				CASE WHEN ISNULL(IJ.Welder1ITSID,'')<>'' then IJ.Welder1ITSID 
					 ELSE '' end as Welder1ITSID,
				CASE WHEN ISNULL(IJ.Welder2ITSID,'')<>'' then IJ.Welder2ITSID 
					 ELSE '' end as Welder2ITSID,
				CASE WHEN ISNULL(IJ.Welder3ITSID,'')<>'' then IJ.Welder3ITSID 
					 ELSE '' end as Welder3ITSID,
				CASE WHEN ISNULL(IJ.Welder4ITSID,'')<>'' then IJ.Welder4ITSID
					 ELSE '' end as Welder4ITSID,
				CASE WHEN ISNULL(IJ.Welder1Name,'')<>'' then IJ.Welder1Name 
					 ELSE '' end as Welder1Name,
				CASE WHEN ISNULL(IJ.Welder2Name,'')<>'' then IJ.Welder2Name 
					 ELSE '' end as Welder2Name,
				CASE WHEN ISNULL(IJ.Welder3Name,'')<>'' then IJ.Welder3Name 
					 ELSE '' end as Welder3Name,
				CASE WHEN ISNULL(IJ.Welder4Name,'')<>'' then IJ.Welder4Name
					 ELSE '' end as Welder4Name,
				IJ.RootRodClass,IJ.RootLotNumber,
				IJ.HotRodClass,IJ.HotLotNumber,
				IJ.FillerRodClass,IJ.FillerLotNumber,
				IJ.CapRodClass,IJ.CapLotNumber,
				IJ.PreHeat,IJ.Temperature,IJ.PartiallyCompleted,		
				CASE WHEN ISNULL(IJ.IsWeldUnlocked,0)=1 then 'YES'
					 ELSE '' END as IsUnlocked,
				IJ.TieInWeld,IJ.Prefab,
				IJ.Alignment,IJ.Gap,IJ.FinalWeld,
				IJ.WeldingProcess,IJ.JointFitUp,IJ.LineupClamp,IJ.PreweldCleanliness,IJ.MiterJoint,IJ.Degrees,
				IJ.Tacks,IJ.RootPass,IJ.InsideAccess,IJ.InsideInspected,IJ.SubfillPasses,IJ.CapHP,IJ.VisualInspResult,IJ.Comments,
			   CASE WHEN IJ.JointID in (select items from dbo.Split((Select STUFF((SELECT distinct ',' + WeldSerialNumbers
																			 FROM TransmissionWorkOrderSketchMultiple
																			 where ISNULL(WeldSerialNumbers,'')<>'' and IsActive=1 and TransmissionWorkOrderID=WO.TransmissionWorkOrderID
																			FOR XML PATH(''), TYPE
																			).value('.', 'NVARCHAR(MAX)')
																		,1,1,'')),',')) then 'Yes'
					ELSE 'No' end as AddedtoWeldMap,	
				CASE WHEN ISNULL(ISNULL(NDE.ModifiedBy,NDE.CreatedBy),0)>0 then isnull((select ContractorDisplayName from ContractorMaster where VenderCode=(select top 1 VendorCode from [OAMSCM].dbo.LoginMaster where LoginMasterID=ISNULL(ISNULL(NDE.ModifiedBy,NDE.CreatedBy),0))),'') else CMNDE.ContractorDisplayName end as NDEContractorName,
				NDE.RTInterpreter as NDEInspectorName,
				Convert(nvarchar,NDE.RadiographedDate,101) as RadiographedDateDT,
				NDE.RTReportNumber,	
				case when NDE.NDEStatusDesc='Submit for Review' and NDE.NDEStatusbyFilmStatus IN ('Accept','Accepted') then 'Accept' 
					 when NDE.NDEStatusDesc='Submit for Review' and NDE.NDEStatusbyFilmStatus IN ('Reject','Rejected') then 'Reject' 
					 when NDE.NDEStatusDesc='In Process' then 'In Process'
					 when NDE.NDEStatusDesc='Pending' then 'Pending' 
					else '' end as NDEStatus,
				case when NDE.NDEStatusDesc='Submit for Review' and NDE.NDEStatusbyFilmStatus IN ('Accept','Reject','Accepted','Rejected') then NDECompletionDate 
					 else '' end as NDECompletionDate,
				CASE WHEN ISNULL(NDE.CRIModifiedBy,0)>0 then isnull((select ContractorDisplayName from ContractorMaster where VenderCode=(select top 1 VendorCode from [OAMSCM].dbo.LoginMaster where LoginMasterID=ISNULL(NDE.CRIModifiedBy,0))),'') else CMCRI.ContractorDisplayName end as CRIContractorName,
				ISNULL((SELECT TOP 1 FWFO.CRIEmployeeName
							 from FieldWeldFilmDetails FWFO  
							 inner join FWRTInspectionDetails FTO on FTO.FWRTInspectionDetailsID=FWFO.FWRTInspectionDetailsID  
							 where FTO.TransmissionWorkOrderID=WO.TransmissionWorkOrderID and FTO.RTInspectionID=NDE.RTInspectionID order by FWFO.CRIModifiedDate DESC),'') as CRIInspectorName,		 
				case when NDE.CRIStatusDesc IN ('Accept','Accepted') and NDE.CRIWeldCheck='Accept' then 'Accept' 
					 when NDE.CRIStatusDesc IN ('Accept','Accepted') and NDE.CRIWeldCheck='Reject' then 'Reject' 
					 when NDE.CRIStatusDesc IN ('Reject','Rejected') then 'Reject' 
					 when NDE.CRIStatusDesc='In Process' then 'In Process'
					 when NDE.CRIStatusDesc='Pending' then 'Pending' 
					 else '' end AS CRIStatus,
				 case when CRIStatusDesc IN ('Completed','Accepted','Rejected') then CRICompletionDate else '' end as CRICompletionDate,
				 CASE WHEN ISNULL(NDE.TertiaryCrewDesc,'')='Company' then 'Company'
					  WHEN ISNULL(NDE.TertiaryCrewDesc,'')='Contractor' then CASE WHEN ISNULL(NDE.TertiaryContractorMasterID,0)<>0 then isnull((select top 1 ContractorDisplayName from ContractorMaster where ContractorMasterID=NDE.TertiaryContractorMasterID),'')																													  ELSE 'Contractor' end
					  ELSE '' end as TRCrew,
				 NDE.ApproverName as TRName,
				 case when NDE.Level3StatusDesc IN ('Accept','Accepted','Approved') then 'Approved'
					 when NDE.Level3StatusDesc IN ('Reject','Rejected') then 'Rejected' 
					 when ISNULL(NDE.TertiaryCrewDesc,'')<>'' and NDE.Level3StatusDesc='Pending' then 'Pending' 
					 else '' end as TRStatus,
				 case when Level3StatusDesc IN ('Accept','Reject','Accepted','Rejected', 'Approved') then Level3CompletionDate else '' end as TRCompletionDate,
				 NDE.RTReportNumberandType
				FROM TransmissionISOMainJoint IJ 
					INNER JOIN TransmissionISO I ON IJ.TransmissionISOID = I.TransmissionISOID 
					INNER JOIN TransmissionWorkOrder AS WO ON WO.TransmissionWorkOrderID=I.TransmissionWorkOrderID and WO.IsActive=1 and WO.IsDeleted=0
					LEFT JOIN ContractorMaster AS CM ON CM.ContractorMasterID=WO.ContractorMasterID
					LEFT JOIN ContractorMaster CMC ON CMC.ContractorMasterID = WO.ContractorInspectorMasterID  
					LEFT JOIN ContractorMaster CMNDE ON CMNDE.ContractorMasterID = WO.ContractorRTMasterID  
					LEFT JOIN ContractorMaster CMCRI ON CMCRI.ContractorMasterID = WO.ContractorCRIMasterID  
					Left join TransmissionWeldType as TWT on TWT.ID=IJ.WeldType     
					LEFT JOIN (select RTInspectionID,TransmissionWorkOrderID,RTReportNumber,RTReportNumber + ' (Conv)' as RTReportNumberandType,RTInterpreter,
								JobSiteLocation,RTReportStatus,FieldWelds,NumberofFilms,
								RadiographedDate,RadiographedDateDT,CRIStatus,TertiaryCrewDesc,TertiaryContractorMasterID,ApprovalStatus,ApproverName,ApproverRemarks,
								NDERejectedWeldsQty,ReshootRequired,ReshootActionRequired,ReshootUpdated,ReshootCount,FWNumbers,
								NDEStatusDesc,CRIStatusDesc,Level3StatusDesc,
								case when NDEStatusDesc='Submit for Review' and NDEStatusbyFilmStatus IN ('Accept','Reject','Accepted','Rejected') then NDECompletionDate 
									 else '' end as NDECompletionDate,
								case when CRIStatusDesc IN ('Completed','Accepted','Rejected') then CRICompletionDate else '' end as CRICompletionDate,
								case when ApprovalStatus IN ('Accept','Reject','Accepted','Rejected') then Level3CompletionDate else '' end as Level3CompletionDate,
								NDEStatusbyFilmStatus,CRIFilmQuality,CRIWeldCheck,
								CreatedBy,ModifiedBy,CRIModifiedBy
								from
								(select *, 
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' then 'Pending'
									 else RTReportStatus end as NDEStatusDesc,
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootUpdated=1 and ReshootCount=1 then 'Pending'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' and ReshootUpdated=0 and ReshootCount=1 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=2 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='NO' and ReshootCount=1 and ReshootUpdated=1 then 'Accepted'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=0 then 'Accepted'
									 when ISNULL(CRIStatus,'')= '' and ISNULL(RTReportStatus,'')= 'Submit for Review' then 'Pending'
									 else CRIStatus end as CRIStatusDesc,
								case when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootCount=2 then 'Pending'
									 when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ISNULL(ReshootRequired,'')<>'YES' then 'Pending'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 when ISNULL(ApprovalStatus,'')= 'Accept' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Accepted' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Approved' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 else '' end as Level3StatusDesc
								from 
								(Select distinct RT.RTInspectionID,RT.TransmissionWorkOrderID,RT.RTReportNumber,RT.RTInterpreter,RT.JobSiteLocation,RT.RTInspectionStatus as RTReportStatus,
								ISNULL((select count(distinct FWRTInspectionDetailsID) from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0),0) as FieldWelds,
								ISNULL((select count(distinct FieldWeldFilmDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and IsDeleted=0),0) as NumberofFilms,
								RT.RadiographedDate, Convert(nvarchar,RT.RadiographedDate,101) as RadiographedDateDT,
								RT.CRIStatus,RT.TertiaryCrewDesc,RT.TertiaryContractorMasterID,RT.ApprovalStatus,RT.ApproverName,RT.ApproverRemarks,
								ISNULL((select count(distinct FWRTInspectionDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and Result='Reject' and IsDeleted=0),0) as NDERejectedWeldsQty,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldFilmDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootRequired,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldFilmDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and ReshootActionRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootActionRequired,
								CASE WHEN ISNULL((select count(distinct FieldWeldFilmDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) = ISNULL((select count(distinct FieldWeldFilmDetailsID) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and ReshootUpdated=1 and IsDeleted=0),0) then 1
									 ELSE 0 END as ReshootUpdated,
								ISNULL((select max(distinct ReshootCount) from FieldWeldFilmDetails where FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0) and IsDeleted=0),0) as ReshootCount,
								STUFF((SELECT distinct '; ' + TMJ.JointID  
										FROM TransmissionISOMainJoint TMJ   
										where TMJ.TransmissionISOMainJointID in (select distinct FieldWeldID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0)  
									   FOR XML PATH(''), TYPE  
									   ).value('.', 'NVARCHAR(MAX)')  
									  ,1,2,'') FWNumbers,
								CASE WHEN ISNULL(RT.ModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ModifiedDate,101)
									 ELSE Convert(nvarchar,RT.CreatedDate,101) END as NDECompletionDate,
								CASE WHEN ISNULL(RT.CRIModifiedDate,'')<>'' THEN Convert(nvarchar,RT.CRIModifiedDate,101)
									 ELSE '' END as CRICompletionDate,
								CASE WHEN ISNULL(RT.ApproverModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ApproverModifiedDate,101)
									 ELSE '' END as Level3CompletionDate,
								CASE WHEN exists((select FieldWeldFilmDetailsID from FieldWeldFilmDetails where IsDeleted=0 and isnull(Result,'')<>'' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldFilmDetailsID) from FieldWeldFilmDetails where IsDeleted=0 and isnull(Result,'')='Reject' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as NDEStatusbyFilmStatus,
								CASE WHEN exists((select FieldWeldFilmDetailsID from FieldWeldFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')<>'' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldFilmDetailsID) from FieldWeldFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0)),0)>0 then 'Fail'
													  else 'Pass' end
											else '' end as CRIFilmQuality,
								CASE WHEN exists((select FieldWeldFilmDetailsID from FieldWeldFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0))) then 'Reject'
									 WHEN exists((select FieldWeldFilmDetailsID from FieldWeldFilmDetails where IsDeleted=0 and isnull(CRIResult,'')<>'' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldFilmDetailsID) from FieldWeldFilmDetails where IsDeleted=0 and isnull(CRIResult,'')='Reject' and FWRTInspectionDetailsID in (select distinct FWRTInspectionDetailsID from FWRTInspectionDetails where RTInspectionID=RT.RTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as CRIWeldCheck,
								RT.CreatedBy, RT.ModifiedBy, RT.CRIModifiedBy
								FROM RTInspectionDetails AS RT 
								Where RT.IsActive=1
								) as result)as outerresult
								union
								select CMPRRTInspectionID as RTInspectionID,TransmissionWorkOrderID,RTReportNumber,RTReportNumber + ' (CR)' as RTReportNumberandType,RTInterpreter,
								JobSiteLocation,RTReportStatus,FieldWelds,NumberofFilms,
								RadiographedDate,RadiographedDateDT,CRIStatus,TertiaryCrewDesc,TertiaryContractorMasterID,ApprovalStatus,ApproverName,ApproverRemarks,
								NDERejectedWeldsQty,ReshootRequired,ReshootActionRequired,ReshootUpdated,ReshootCount,FWNumbers,
								NDEStatusDesc,CRIStatusDesc,Level3StatusDesc,
								case when NDEStatusDesc='Submit for Review' and NDEStatusbyFilmStatus IN ('Accept','Reject','Accepted','Rejected') then NDECompletionDate 
									 else '' end as NDECompletionDate,
								case when CRIStatusDesc IN ('Completed','Accepted','Rejected') then CRICompletionDate else '' end as CRICompletionDate,
								case when ApprovalStatus IN ('Accept','Reject','Accepted','Rejected') then Level3CompletionDate else '' end as Level3CompletionDate,
								NDEStatusbyFilmStatus,CRIFilmQuality,CRIWeldCheck,
								CreatedBy,ModifiedBy,CRIModifiedBy
								from
								(select *, 
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' then 'Pending'
									 else RTReportStatus end as NDEStatusDesc,
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootUpdated=1 and ReshootCount=1 then 'Pending'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' and ReshootUpdated=0 and ReshootCount=1 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=2 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='NO' and ReshootCount=1 and ReshootUpdated=1 then 'Accepted'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=0 then 'Accepted'
									 when ISNULL(CRIStatus,'')= '' and ISNULL(RTReportStatus,'')= 'Submit for Review' then 'Pending'
									 else CRIStatus end as CRIStatusDesc,
								case when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootCount=2 then 'Pending'
									 when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ISNULL(ReshootRequired,'')<>'YES' then 'Pending'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 when ISNULL(ApprovalStatus,'')= 'Accept' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Accepted' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Approved' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 else '' end as Level3StatusDesc
								from 
								(Select distinct RT.CMPRRTInspectionID,RT.TransmissionWorkOrderID,RT.RTReportNumber,RT.RTInterpreter,RT.JobSiteLocation,RT.CMPRRTInspectionStatus as RTReportStatus,
								ISNULL((select count(distinct FWCMPRRTInspectionDetailsID) from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0),0) as FieldWelds,
								ISNULL((select count(distinct FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and IsDeleted=0),0) as NumberofFilms,
								RT.RadiographedDate, Convert(nvarchar,RT.RadiographedDate,101) as RadiographedDateDT,
								RT.CRIStatus,RT.TertiaryCrewDesc,RT.TertiaryContractorMasterID,RT.ApprovalStatus,RT.ApproverName,RT.ApproverRemarks,
								ISNULL((select count(distinct FWCMPRRTInspectionDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and Result='Reject' and IsDeleted=0),0) as NDERejectedWeldsQty,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootRequired,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and ReshootActionRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootActionRequired,
								CASE WHEN ISNULL((select count(distinct FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) = ISNULL((select count(distinct FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and ReshootUpdated=1 and IsDeleted=0),0) then 1
									 ELSE 0 END as ReshootUpdated,
								ISNULL((select max(distinct ReshootCount) from FieldWeldCMPRFilmDetails where FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0) and IsDeleted=0),0) as ReshootCount,
								STUFF((SELECT distinct '; ' + TMJ.JointID  
										FROM TransmissionISOMainJoint TMJ   
										where TMJ.TransmissionISOMainJointID in (select distinct FieldWeldID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0)  
									   FOR XML PATH(''), TYPE  
									   ).value('.', 'NVARCHAR(MAX)')  
									  ,1,2,'') FWNumbers,
								CASE WHEN ISNULL(RT.ModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ModifiedDate,101)
									 ELSE Convert(nvarchar,RT.CreatedDate,101) END as NDECompletionDate,
								CASE WHEN ISNULL(RT.CRIModifiedDate,'')<>'' THEN Convert(nvarchar,RT.CRIModifiedDate,101)
									 ELSE '' END as CRICompletionDate,
								CASE WHEN ISNULL(RT.ApproverModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ApproverModifiedDate,101)
									 ELSE '' END as Level3CompletionDate,
								CASE WHEN exists((select FieldWeldCMPRFilmDetailsID from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(Result,'')<>'' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(Result,'')='Reject' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as NDEStatusbyFilmStatus,
								CASE WHEN exists((select FieldWeldCMPRFilmDetailsID from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')<>'' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0)),0)>0 then 'Fail'
													  else 'Pass' end
											else '' end as CRIFilmQuality,
								CASE WHEN exists((select FieldWeldCMPRFilmDetailsID from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0))) then 'Reject'
									 WHEN exists((select FieldWeldCMPRFilmDetailsID from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(CRIResult,'')<>'' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldCMPRFilmDetailsID) from FieldWeldCMPRFilmDetails where IsDeleted=0 and isnull(CRIResult,'')='Reject' and FWCMPRRTInspectionDetailsID in (select distinct FWCMPRRTInspectionDetailsID from FWCMPRRTInspectionDetails where CMPRRTInspectionID=RT.CMPRRTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as CRIWeldCheck,
								RT.CreatedBy, RT.ModifiedBy, RT.CRIModifiedBy
								FROM CMPRRTInspectionDetails AS RT 
								Where RT.IsActive=1
								) as result)as outerresult
								union
								select DIGRRTInspectionID as RTInspectionID,TransmissionWorkOrderID,RTReportNumber,RTReportNumber + ' (DR)' as RTReportNumberandType,RTInterpreter,
								JobSiteLocation,RTReportStatus,FieldWelds,NumberofFilms,
								RadiographedDate,RadiographedDateDT,CRIStatus,TertiaryCrewDesc,TertiaryContractorMasterID,ApprovalStatus,ApproverName,ApproverRemarks,
								NDERejectedWeldsQty,ReshootRequired,ReshootActionRequired,ReshootUpdated,ReshootCount,FWNumbers,
								NDEStatusDesc,CRIStatusDesc,Level3StatusDesc,
								case when NDEStatusDesc='Submit for Review' and NDEStatusbyFilmStatus IN ('Accept','Reject','Accepted','Rejected') then NDECompletionDate 
									 else '' end as NDECompletionDate,
								case when CRIStatusDesc IN ('Completed','Accepted','Rejected') then CRICompletionDate else '' end as CRICompletionDate,
								case when ApprovalStatus IN ('Accept','Reject','Accepted','Rejected') then Level3CompletionDate else '' end as Level3CompletionDate,
								NDEStatusbyFilmStatus,CRIFilmQuality,CRIWeldCheck,
								CreatedBy,ModifiedBy,CRIModifiedBy
								from
								(select *, 
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' then 'Pending'
									 else RTReportStatus end as NDEStatusDesc,
								case when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootUpdated=1 and ReshootCount=1 then 'Pending'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootActionRequired='YES' and ReshootUpdated=0 and ReshootCount=1 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=2 then 'Rejected'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='NO' and ReshootCount=1 and ReshootUpdated=1 then 'Accepted'
									 when ISNULL(CRIStatus,'')= 'Completed' and ReshootCount=0 then 'Accepted'
									 when ISNULL(CRIStatus,'')= '' and ISNULL(RTReportStatus,'')= 'Submit for Review' then 'Pending'
									 else CRIStatus end as CRIStatusDesc,
								case when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ReshootRequired='YES' and ReshootCount=2 then 'Pending'
									 when ISNULL(ApprovalStatus,'')= '' and ISNULL(CRIStatus,'')= 'Completed' and ISNULL(ReshootRequired,'')<>'YES' then 'Pending'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 when ISNULL(ApprovalStatus,'')= 'Accept' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Accepted' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Approved' then 'Approved'
									 when ISNULL(ApprovalStatus,'')= 'Reject' then 'Rejected'
									 else '' end as Level3StatusDesc
								from 
								(Select distinct RT.DIGRRTInspectionID,RT.TransmissionWorkOrderID,RT.RTReportNumber,RT.RTInterpreter,RT.JobSiteLocation,RT.DIGRRTInspectionStatus as RTReportStatus,
								ISNULL((select count(distinct FWDIGRRTInspectionDetailsID) from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0),0) as FieldWelds,
								ISNULL((select count(distinct FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and IsDeleted=0),0) as NumberofFilms,
								RT.RadiographedDate, Convert(nvarchar,RT.RadiographedDate,101) as RadiographedDateDT,
								RT.CRIStatus,RT.TertiaryCrewDesc,RT.TertiaryContractorMasterID,RT.ApprovalStatus,RT.ApproverName,RT.ApproverRemarks,
								ISNULL((select count(distinct FWDIGRRTInspectionDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and Result='Reject' and IsDeleted=0),0) as NDERejectedWeldsQty,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootRequired,
								CASE WHEN ISNULL(RT.CRIStatus,'')<> '' THEN
																		CASE WHEN ISNULL((select count(distinct FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and ReshootActionRequired=1 and IsDeleted=0),0) > 0 then 'YES'
																		ELSE 'NO' END
									 ELSE '' END as ReshootActionRequired,
								CASE WHEN ISNULL((select count(distinct FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and ReshootRequired=1 and IsDeleted=0),0) = ISNULL((select count(distinct FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and ReshootUpdated=1 and IsDeleted=0),0) then 1
									 ELSE 0 END as ReshootUpdated,
								ISNULL((select max(distinct ReshootCount) from FieldWeldDIGRFilmDetails where FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0) and IsDeleted=0),0) as ReshootCount,
								STUFF((SELECT distinct '; ' + TMJ.JointID  
										FROM TransmissionISOMainJoint TMJ   
										where TMJ.TransmissionISOMainJointID in (select distinct FieldWeldID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0)  
									   FOR XML PATH(''), TYPE  
									   ).value('.', 'NVARCHAR(MAX)')  
									  ,1,2,'') FWNumbers,
								CASE WHEN ISNULL(RT.ModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ModifiedDate,101)
									 ELSE Convert(nvarchar,RT.CreatedDate,101) END as NDECompletionDate,
								CASE WHEN ISNULL(RT.CRIModifiedDate,'')<>'' THEN Convert(nvarchar,RT.CRIModifiedDate,101)
									 ELSE '' END as CRICompletionDate,
								CASE WHEN ISNULL(RT.ApproverModifiedDate,'')<>'' THEN Convert(nvarchar,RT.ApproverModifiedDate,101)
									 ELSE '' END as Level3CompletionDate,
								CASE WHEN exists((select FieldWeldDIGRFilmDetailsID from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(Result,'')<>'' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(Result,'')='Reject' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as NDEStatusbyFilmStatus,
								CASE WHEN exists((select FieldWeldDIGRFilmDetailsID from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')<>'' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0)),0)>0 then 'Fail'
													  else 'Pass' end
											else '' end as CRIFilmQuality,
								CASE WHEN exists((select FieldWeldDIGRFilmDetailsID from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(FilmQuality,'')='Fail' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0))) then 'Reject'
									 WHEN exists((select FieldWeldDIGRFilmDetailsID from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(CRIResult,'')<>'' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0))) 
											then case when isnull((select count(FieldWeldDIGRFilmDetailsID) from FieldWeldDIGRFilmDetails where IsDeleted=0 and isnull(CRIResult,'')='Reject' and FWDIGRRTInspectionDetailsID in (select distinct FWDIGRRTInspectionDetailsID from FWDIGRRTInspectionDetails where DIGRRTInspectionID=RT.DIGRRTInspectionID and IsDeleted=0)),0)>0 then 'Reject'
													  else 'Accept' end
											else '' end as CRIWeldCheck,
								RT.CreatedBy, RT.ModifiedBy, RT.CRIModifiedBy
								FROM DIGRRTInspectionDetails AS RT 
								Where RT.IsActive=1
								) as result)as outerresult) NDE on NDE.TransmissionWorkOrderID=WO.TransmissionWorkOrderID and NDE.RTInspectionID in (select distinct RTInspectionID from FWRTInspectionDetails where FieldWeldID=IJ.TransmissionISOMainJointID and IsDeleted=0
																																					 union
																																					 select distinct CMPRRTInspectionID from FWCMPRRTInspectionDetails where FieldWeldID=IJ.TransmissionISOMainJointID and IsDeleted=0
																																					 union
																																					 select distinct DIGRRTInspectionID from FWDIGRRTInspectionDetails where FieldWeldID=IJ.TransmissionISOMainJointID and IsDeleted=0)				
				) as res
				order by ProjectNumber,WorkOrderNumber,WeldSerialNumber desc"""
    
    
import pyodbc
from azure.identity import AzureCliCredential, DefaultAzureCredential
import pandas as pd
from datetime import datetime
import struct
import logging
import time  # ✅ ADDED: Missing import
from typing import Dict, Any, List, Tuple

# Suppress Azure Identity verbose logging
logging.getLogger('azure.identity').setLevel(logging.ERROR)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

# Global token cache for Fabric connection
_token_cache = {
    "token": None,
    "expires_at": 0
}


def get_fabric_token(force_refresh=False):
    """Get or refresh Microsoft Fabric access token with caching."""
    global _token_cache
    
    current_time = time.time()
    
    if not force_refresh and _token_cache["token"] and current_time < (_token_cache["expires_at"] - 300):
        print(f"[Fabric] Using cached token")
        return _token_cache["token"]
    
    print("[Fabric] Acquiring new token")
    
    try:
        try:
            credential = AzureCliCredential()
            token_response = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            print("[Fabric] ✅ Using Azure CLI credential")
        except Exception as cli_error:
            print(f"[Fabric] Azure CLI failed: {str(cli_error)}")
            credential = DefaultAzureCredential(
                exclude_visual_studio_code_credential=True,
                exclude_powershell_credential=True,
                exclude_shared_token_cache_credential=True,
                exclude_workload_identity_credential=True,
                exclude_developer_cli_credential=True
            )
            token_response = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            print("[Fabric] Using DefaultAzureCredential")
        
        _token_cache["token"] = token_response.token
        _token_cache["expires_at"] = token_response.expires_on
        
        print(f"[Fabric] ✅ Token acquired")
        return token_response.token
        
    except Exception as e:
        print(f"[Fabric] ❌ Token acquisition failed: {str(e)}")
        raise Exception(f"Token acquisition failed: {str(e)}")


def get_sql_server_connection():
    """
    Create connection to SQL Server using SQL authentication.
    
    Returns:
        pyodbc.Connection: Active SQL Server connection
    """
    try:
        server = "10.0.1.9"
        database = "CEDEMONEW0314"
        username = "QuadrantAIUser"
        password = "QU1R19T19E19@12"
        
        print(f"[SQL Server] Connecting to {server}/{database}")
        
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
        )
        
        conn = pyodbc.connect(connection_string, timeout=30)
        print("[SQL Server] ✅ Connection established")
        return conn
        
    except pyodbc.Error as e:
        print(f"[SQL Server] ❌ Connection error: {str(e)}")
        raise Exception(f"SQL Server connection failed: {str(e)}")


def get_fabric_connection():
    """
    Create connection to Microsoft Fabric warehouse.
    
    Returns:
        pyodbc.Connection: Active Fabric connection
    """
    try:
        server = "w3qy24yijqqencf2hpyf3pxrf4-6trn5wecf2euff2i4t5hv6xiy4.datawarehouse.fabric.microsoft.com"
        database = "Gold_WH"
        
        print(f"[Fabric] Connecting to {server}/{database}")
        
        token_str = get_fabric_token()
        token_bytes = token_str.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"PORT=1433;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        print("[Fabric] ✅ Connection established")
        return conn
        
    except Exception as e:
        print(f"[Fabric] ❌ Connection error: {str(e)}")
        raise Exception(f"Fabric connection failed: {str(e)}")


def execute_query(conn, query: str, source: str) -> pd.DataFrame:
    """
    Execute query and return results as pandas DataFrame.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        source: Source name for logging (SQL Server or Fabric)
    
    Returns:
        pd.DataFrame: Query results
    """
    try:
        print(f"[{source}] Executing query...")
        df = pd.read_sql(query, conn)
        print(f"[{source}] ✅ Retrieved {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"[{source}] ❌ Query execution failed: {str(e)}")
        raise


def compare_dataframes(df_sql: pd.DataFrame, df_fabric: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare two dataframes and return detailed comparison results.
    
    Args:
        df_sql: DataFrame from SQL Server
        df_fabric: DataFrame from Fabric
    
    Returns:
        Dict: Comparison results
    """
    print("\n" + "="*80)
    print("DATA VALIDATION RESULTS")
    print("="*80)
    
    results = {
        "row_count_match": False,
        "column_count_match": False,
        "column_names_match": False,
        "data_match": False,
        "sql_row_count": len(df_sql),
        "fabric_row_count": len(df_fabric),
        "sql_columns": list(df_sql.columns),
        "fabric_columns": list(df_fabric.columns),
        "missing_in_fabric": [],
        "missing_in_sql": [],
        "data_differences": []
    }
    
    # Row count comparison
    print(f"\n📊 ROW COUNT COMPARISON:")
    print(f"   SQL Server: {results['sql_row_count']} rows")
    print(f"   Fabric:     {results['fabric_row_count']} rows")
    results["row_count_match"] = results['sql_row_count'] == results['fabric_row_count']
    print(f"   Match: {'✅ YES' if results['row_count_match'] else '❌ NO'}")
    
    # Column comparison
    print(f"\n📋 COLUMN COMPARISON:")
    print(f"   SQL Server: {len(df_sql.columns)} columns")
    print(f"   Fabric:     {len(df_fabric.columns)} columns")
    results["column_count_match"] = len(df_sql.columns) == len(df_fabric.columns)
    
    # Normalize column names for comparison (case-insensitive)
    sql_cols_lower = {col.lower(): col for col in df_sql.columns}
    fabric_cols_lower = {col.lower(): col for col in df_fabric.columns}
    
    missing_in_fabric = [sql_cols_lower[col] for col in sql_cols_lower if col not in fabric_cols_lower]
    missing_in_sql = [fabric_cols_lower[col] for col in fabric_cols_lower if col not in sql_cols_lower]
    
    results["missing_in_fabric"] = missing_in_fabric
    results["missing_in_sql"] = missing_in_sql
    results["column_names_match"] = len(missing_in_fabric) == 0 and len(missing_in_sql) == 0
    
    if missing_in_fabric:
        print(f"\n   ❌ Columns in SQL Server but NOT in Fabric:")
        for col in missing_in_fabric:
            print(f"      - {col}")
    
    if missing_in_sql:
        print(f"\n   ❌ Columns in Fabric but NOT in SQL Server:")
        for col in missing_in_sql:
            print(f"      - {col}")
    
    if results["column_names_match"]:
        print(f"   ✅ All columns match!")
    
    # Data comparison (if columns and row counts match)
    if results["row_count_match"] and results["column_names_match"]:
        print(f"\n🔍 DATA CONTENT COMPARISON:")
        
        # Align dataframes with matching columns (case-insensitive)
        common_cols = [sql_cols_lower[col] for col in sql_cols_lower if col in fabric_cols_lower]
        
        # Create copies with normalized column names for comparison
        df_sql_compare = df_sql[common_cols].copy()
        df_fabric_compare = df_fabric[[fabric_cols_lower[col.lower()] for col in common_cols]].copy()
        df_fabric_compare.columns = common_cols  # Align column names
        
        # Sort both dataframes by a key column if exists
        key_col = None
        for potential_key in ['WeldSerialNumber', 'TransmissionWorkOrderID', 'ProjectNumber']:
            if potential_key in common_cols:
                key_col = potential_key
                break
        
        if key_col:
            df_sql_compare = df_sql_compare.sort_values(key_col).reset_index(drop=True)
            df_fabric_compare = df_fabric_compare.sort_values(key_col).reset_index(drop=True)
            print(f"   Sorted by: {key_col}")
        
        # Convert to string for comparison (handles null/None differences)
        df_sql_str = df_sql_compare.astype(str).fillna('')
        df_fabric_str = df_fabric_compare.astype(str).fillna('')
        
        # Compare cell by cell
        differences = []
        for idx in range(len(df_sql_str)):
            for col in common_cols:
                sql_val = df_sql_str.iloc[idx][col]
                fabric_val = df_fabric_str.iloc[idx][col]
                
                if sql_val != fabric_val:
                    differences.append({
                        "row": idx,
                        "column": col,
                        "sql_value": sql_val,
                        "fabric_value": fabric_val
                    })
        
        results["data_differences"] = differences
        results["data_match"] = len(differences) == 0
        
        if results["data_match"]:
            print(f"   ✅ All data matches perfectly!")
        else:
            print(f"   ❌ Found {len(differences)} data differences")
            print(f"\n   Showing first 10 differences:")
            for diff in differences[:10]:
                print(f"      Row {diff['row']}, Column '{diff['column']}':")
                print(f"         SQL:    '{diff['sql_value']}'")
                print(f"         Fabric: '{diff['fabric_value']}'")
    
    else:
        print(f"\n⚠️  Skipping detailed data comparison (row/column mismatch)")
    
    # Overall result
    print(f"\n" + "="*80)
    all_match = (results["row_count_match"] and 
                 results["column_names_match"] and 
                 results["data_match"])
    
    if all_match:
        print("✅ VALIDATION PASSED: SQL Server and Fabric data are identical!")
    else:
        print("❌ VALIDATION FAILED: Differences found between SQL Server and Fabric")
    print("="*80 + "\n")
    
    return results


def main():
    """Main validation function."""
    try:
        # Import the SQL query for SQL Server
        from testing_welddetails import SQL as sql_server_query
        
        print("🚀 Starting Data Validation: SQL Server vs Fabric Warehouse")
        print("="*80)
        
        # Connect to both databases
        print("\n📡 Establishing connections...")
        sql_conn = get_sql_server_connection()
        fabric_conn = get_fabric_connection()
        
        # Execute query on SQL Server - run the complex query as-is
        print("\n📥 Fetching data from SQL Server (complex query with possible duplicates)...")
        df_sql = execute_query(sql_conn, sql_server_query, "SQL Server")
        
        # Execute query on Fabric - get specific columns from welddetails
        print("\n📥 Fetching data from Fabric Warehouse...")
        fabric_query = """
        SELECT 
            TransmissionWorkOrderID,
            ProjectNumber,
            WorkOrderNumber, 
            WeldCategory,
            WeldSerialNumber,
            CWIName,
            Completed,
            WeldCompletionDateTime,
            CWIResult,
            NDEInspectorName,
            NDEStatus,
            NDECompletionDate,
            CRIInspectorName,
            CRIStatus,
            CRICompletionDate
        FROM welddetails 
        ORDER BY ProjectNumber, WorkOrderNumber, WeldSerialNumber DESC
        """
        
        df_fabric = execute_query(fabric_conn, fabric_query, "Fabric")
        
        # Close connections
        sql_conn.close()
        fabric_conn.close()
        
        # Filter SQL Server data to only include the same columns as Fabric
        columns_to_compare = [
            'TransmissionWorkOrderID',
            'ProjectNumber',
            'WorkOrderNumber', 
            'WeldCategory',
            'WeldSerialNumber',
            'CWIName',
            'Completed',
            'WeldCompletionDateTime',
            'CWIResult',
            'NDEInspectorName',
            'NDEStatus',
            'NDECompletionDate',
            'CRIInspectorName',
            'CRIStatus',
            'CRICompletionDate'
        ]
        
        print(f"\n📋 Filtering SQL Server data to match Fabric columns...")
        # Filter SQL data to only include columns that exist in both
        df_sql_filtered = df_sql[columns_to_compare].copy()
        
        print(f"\n📊 Data Summary:")
        print(f"   SQL Server: {len(df_sql_filtered)} records (includes duplicates from complex query)")
        print(f"   Fabric:     {len(df_fabric)} records")
        print(f"   Columns:    {len(columns_to_compare)} columns to compare")
        
        # Compare data directly
        results = compare_dataframes(df_sql_filtered, df_fabric)
        
        # Save results to CSV for detailed inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_file = f"sql_server_data_{timestamp}.csv"
        fabric_file = f"fabric_data_{timestamp}.csv"
        
        # Save filtered data for comparison
        df_sql_filtered.to_csv(sql_file, index=False)
        df_fabric.to_csv(fabric_file, index=False)
        
        print(f"\n💾 Data exported for manual inspection:")
        print(f"   SQL Server: {sql_file}")
        print(f"   Fabric:     {fabric_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    results = main()